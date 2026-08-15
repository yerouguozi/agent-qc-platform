from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str


class AgentRegisterIn(BaseModel):
    name: str
    mcp_url: str
    rate_limit_qps: int = 5


class AgentOut(BaseModel):
    id: str
    name: str
    mcp_url: str
    rate_limit_qps: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentRegisterOut(AgentOut):
    api_key: str


class ToolOut(BaseModel):
    id: str
    agent_id: str
    name: str
    description: str
    status: str

    model_config = {"from_attributes": True}


class ProxyCallIn(BaseModel):
    agent_id: str
    tool_name: str
    arguments: dict[str, Any] = {}
    session_id: str = ""


class ProxyCallOut(BaseModel):
    trace_id: str
    result: Any
    latency_ms: int
    status: str


class TraceOut(BaseModel):
    id: int
    trace_id: str
    session_id: str
    agent_id: str
    tool_name: str
    params_masked_json: str
    result_summary: str
    status: str
    latency_ms: int
    token_usage: int
    cost: float
    error_code: str | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TraceIngestIn(BaseModel):
    session_id: str = ""
    tool_name: str
    arguments: dict[str, Any] = {}
    result_summary: str = ""
    status: str = "success"
    latency_ms: int = 0
    token_usage: int = 0
    cost: float = 0.0
    error_code: str | None = None
    error_message: str | None = None