import asyncio
import json
import time

from sqlalchemy.orm import Session

from app.gateway.audit import log_audit
from app.gateway.ratelimit import RateLimiter
from app.models import Agent
from app.trace.store import create_trace


class ProxyError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class RateLimitError(ProxyError):
    def __init__(self, agent_id: str):
        super().__init__(429, "RATE_LIMITED", f"rate limit exceeded for agent {agent_id}")


class MCPClient:
    async def list_tools(self) -> list[dict]:
        raise NotImplementedError

    async def call_tool(self, name: str, arguments: dict) -> dict:
        raise NotImplementedError


class StreamableHttpMCPClient(MCPClient):
    def __init__(self, url: str):
        self.url = url

    async def list_tools(self) -> list[dict]:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        async with streamable_http_client(self.url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                return [
                    {"name": t.name, "description": t.description or "", "input_schema": t.inputSchema}
                    for t in tools.tools
                ]

    async def call_tool(self, name: str, arguments: dict) -> dict:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        async with streamable_http_client(self.url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                content = []
                for block in result.content:
                    if block.type == "text":
                        content.append(block.text)
                    else:
                        content.append(json.dumps(block.model_dump(), ensure_ascii=False))
                return {"content": content, "is_error": result.isError}


class Gateway:
    def __init__(self, limiter: RateLimiter | None = None):
        self.limiter = limiter or RateLimiter()

    def forward_sync(
        self,
        db: Session,
        agent: Agent,
        tool_name: str,
        arguments: dict,
        session_id: str = "",
        source: str = "api",
        timeout: float = 30.0,
    ) -> dict:
        return asyncio.run(
            self.forward(db, agent, tool_name, arguments, session_id=session_id, source=source, timeout=timeout)
        )

    async def forward(
        self,
        db: Session,
        agent: Agent,
        tool_name: str,
        arguments: dict,
        session_id: str = "",
        source: str = "api",
        timeout: float = 30.0,
    ) -> dict:
        if not self.limiter.allow(agent.id):
            create_trace(
                db,
                agent_id=agent.id,
                session_id=session_id,
                tool_name=tool_name,
                arguments=arguments,
                status="ratelimited",
                error_code="RATE_LIMITED",
                error_message="rate limit exceeded",
            )
            log_audit(db, agent.id, f"call:{tool_name}", source=source, result="ratelimited")
            raise RateLimitError(agent.id)

        client = StreamableHttpMCPClient(agent.mcp_url)
        start = time.monotonic()
        try:
            result = await asyncio.wait_for(client.call_tool(tool_name, arguments), timeout=timeout)
            latency = int((time.monotonic() - start) * 1000)
            summary = json.dumps(result, ensure_ascii=False)
            trace = create_trace(
                db,
                agent_id=agent.id,
                session_id=session_id,
                tool_name=tool_name,
                arguments=arguments,
                result_summary=summary,
                status="success",
                latency_ms=latency,
            )
            log_audit(db, agent.id, f"call:{tool_name}", source=source, result="success")
            return {"trace_id": trace.trace_id, "result": result, "latency_ms": latency, "status": "success"}
        except asyncio.TimeoutError:
            latency = int((time.monotonic() - start) * 1000)
            trace = create_trace(
                db,
                agent_id=agent.id,
                session_id=session_id,
                tool_name=tool_name,
                arguments=arguments,
                status="timeout",
                latency_ms=latency,
                error_code="TIMEOUT",
                error_message=f"sut timeout after {timeout}s",
            )
            log_audit(db, agent.id, f"call:{tool_name}", source=source, result="timeout")
            raise ProxyError(504, "TIMEOUT", f"sut timeout after {timeout}s")
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            trace = create_trace(
                db,
                agent_id=agent.id,
                session_id=session_id,
                tool_name=tool_name,
                arguments=arguments,
                status="failed",
                latency_ms=latency,
                error_code="SUT_ERROR",
                error_message=str(exc)[:500],
            )
            log_audit(db, agent.id, f"call:{tool_name}", source=source, result="failed")
            raise ProxyError(502, "SUT_ERROR", f"sut call failed: {exc}") from exc