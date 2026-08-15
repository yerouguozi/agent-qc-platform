import pytest

from app.core.config import settings
from app.llm import LLMError, chat_json


def test_chat_json_requires_key(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    with pytest.raises(LLMError):
        chat_json("sys", "user")


def test_chat_json_retries_then_raises(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", "k")
    monkeypatch.setattr(settings, "judge_max_retries", 1)

    class FakeResponse:
        def raise_for_status(self):
            raise RuntimeError("boom")

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.llm.httpx.Client", lambda **kwargs: FakeClient())
    with pytest.raises(LLMError):
        chat_json("sys", "user")


def test_chat_json_parses_dict(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", "k")
    monkeypatch.setattr(settings, "judge_max_retries", 0)

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": '{"score": 5, "reason": "good"}'}}]}

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.llm.httpx.Client", lambda **kwargs: FakeClient())
    result = chat_json("sys", "user")
    assert result["score"] == 5