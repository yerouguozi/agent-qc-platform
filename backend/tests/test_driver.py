from app.eval.driver import CaseOutput, HttpAgentDriver, MockDriver


def test_mock_driver():
    driver = MockDriver(answer="ok", tool_calls=["load_dataset"])
    out = driver.run("问题", "run1")
    assert out.answer == "ok"
    assert out.tool_calls == ["load_dataset"]


def test_http_driver_calls_sut_and_loads_traces(monkeypatch):
    class FakeResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    class FakeClient:
        def __init__(self):
            self.calls = []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, json=None, headers=None):
            self.calls.append(url)
            if url.endswith("/api/sessions"):
                return FakeResponse({"id": "sid-1", "title": "t"})
            return FakeResponse({"content": "答案是 42"})

    fake = FakeClient()
    monkeypatch.setattr("app.eval.driver.httpx.Client", lambda **kwargs: fake)

    class FakeTrace:
        tool_name = "query_sql"
        trace_id = "tr-1"
        result_summary = '{"rows": 10}'

    driver = HttpAgentDriver(chat_url="http://sut", auth_token="tok", trace_loader=lambda sid: [FakeTrace()])
    out = driver.run("问题", "run1")
    assert out.answer == "答案是 42"
    assert out.tool_calls == ["query_sql"]
    assert out.trace_id == "tr-1"
    assert len(fake.calls) == 2