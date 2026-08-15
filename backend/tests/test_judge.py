import pytest

from app.eval.judge import JudgeError, judge_answer


def test_judge_ok(monkeypatch):
    def fake_chat_json(system, user):
        return {"score": 4, "reason": "正确", "issues": []}

    monkeypatch.setattr("app.eval.judge.chat_json", fake_chat_json)
    result = judge_answer("问题", "回答", "期望")
    assert result["score"] == 4


def test_judge_clamps_score(monkeypatch):
    monkeypatch.setattr("app.eval.judge.chat_json", lambda s, u: {"score": 99, "reason": "x", "issues": []})
    assert judge_answer("q", "a", "e")["score"] == 5


def test_judge_error_propagates(monkeypatch):
    from app.llm import LLMError

    def fail(system, user):
        raise LLMError("down")

    monkeypatch.setattr("app.eval.judge.chat_json", fail)
    with pytest.raises(JudgeError):
        judge_answer("q", "a", "e")