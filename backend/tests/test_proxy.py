import pytest
from sqlalchemy.orm import Session

from app.gateway.proxy import Gateway, ProxyError, RateLimitError
from app.models import Trace


class FakeClient:
    def __init__(self, result=None, error=None):
        self.result = result or {"content": ["ok"], "is_error": False}
        self.error = error

    async def call_tool(self, name, arguments):
        if self.error:
            raise self.error
        return self.result


def test_forward_success(monkeypatch, db: Session, sample_agent):
    gateway = Gateway()
    gateway.limiter.set_limit(sample_agent.id, 100)

    def fake_client(url):
        return FakeClient()

    monkeypatch.setattr("app.gateway.proxy.StreamableHttpMCPClient", fake_client)
    result = gateway.forward_sync(db, sample_agent, "query_sql", {"sql": "select 1"}, session_id="s1")
    assert result["status"] == "success"
    assert db.query(Trace).filter(Trace.trace_id == result["trace_id"]).first() is not None


def test_forward_ratelimited(db: Session, sample_agent):
    gateway = Gateway()
    gateway.limiter.set_limit(sample_agent.id, 0)
    with pytest.raises(RateLimitError):
        gateway.forward_sync(db, sample_agent, "query_sql", {}, session_id="s1")
    trace = db.query(Trace).order_by(Trace.id.desc()).first()
    assert trace.status == "ratelimited"


def test_forward_timeout(monkeypatch, db: Session, sample_agent):
    gateway = Gateway()
    gateway.limiter.set_limit(sample_agent.id, 100)

    class SlowClient:
        async def call_tool(self, name, arguments):
            import asyncio

            await asyncio.sleep(5)

    def fake_client(url):
        return SlowClient()

    monkeypatch.setattr("app.gateway.proxy.StreamableHttpMCPClient", fake_client)
    with pytest.raises(ProxyError) as exc_info:
        gateway.forward_sync(db, sample_agent, "query_sql", {}, session_id="s1", timeout=0.05)
    assert exc_info.value.status_code == 504
    assert db.query(Trace).order_by(Trace.id.desc()).first().status == "timeout"