import httpx

from app.eval.checks import CaseOutput


class AgentDriver:
    def run(self, prompt: str, run_id: str) -> CaseOutput:
        raise NotImplementedError


class MockDriver(AgentDriver):
    def __init__(self, answer: str = "mock answer", tool_calls: list[str] | None = None):
        self.answer = answer
        self.tool_calls = tool_calls or ["mock_tool"]

    def run(self, prompt: str, run_id: str) -> CaseOutput:
        return CaseOutput(answer=self.answer, tool_calls=self.tool_calls)


class HttpAgentDriver(AgentDriver):
    """调用真实 Agent 的 chat API，工具调用由 SUT 插桩上报到本平台 ingest。"""

    def __init__(self, chat_url: str, auth_token: str, trace_loader, dataset_id: str = ""):
        self.chat_url = chat_url.rstrip("/")
        self.auth_token = auth_token
        self.trace_loader = trace_loader
        self.dataset_id = dataset_id

    def run(self, prompt: str, run_id: str) -> CaseOutput:
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        session_payload = {"title": f"eval-{run_id[:8]}"}
        if self.dataset_id:
            session_payload["dataset_id"] = self.dataset_id
        with httpx.Client(timeout=120.0, trust_env=False) as client:
            session_resp = client.post(
                f"{self.chat_url}/api/sessions",
                json=session_payload,
                headers=headers,
            )
            session_resp.raise_for_status()
            sid = session_resp.json()["id"]
            msg_resp = client.post(
                f"{self.chat_url}/api/sessions/{sid}/messages",
                json={"prompt": prompt},
                headers=headers,
            )
            msg_resp.raise_for_status()
            answer = msg_resp.json()["content"]
        traces = self.trace_loader(sid)
        tool_calls = [t.tool_name for t in traces]
        trace_id = traces[-1].trace_id if traces else None
        trace_summaries = [t.result_summary[:500] for t in traces]
        return CaseOutput(answer=answer, tool_calls=tool_calls, trace_id=trace_id, trace_summaries=trace_summaries)


def build_driver(db, *, use_mock: bool = False):
    from app.core.config import settings
    from app.trace.store import traces_by_session

    if use_mock or not settings.sut_chat_url:
        return MockDriver()
    return HttpAgentDriver(
        chat_url=settings.sut_chat_url,
        auth_token=settings.sut_auth_token,
        trace_loader=lambda sid: traces_by_session(db, sid),
        dataset_id=settings.sut_dataset_id,
    )