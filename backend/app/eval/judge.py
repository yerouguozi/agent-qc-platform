from app.llm import LLMError, chat_json


class JudgeError(Exception):
    pass


_RUBRIC = (
    "请按 1-5 分评估回答质量(只输出整数):\n"
    "5=完全正确且完整;4=正确但略有遗漏;3=部分正确;2=存在明显错误;1=严重错误或幻觉。\n"
    "评分维度:正确性(事实与工具结果一致)、工具使用恰当性、无幻觉(数字必须有出处)、完整性。\n"
    "必须输出 JSON: {\"score\": int, \"reason\": str, \"issues\": [str]}\n"
    "禁止输出其它内容。"
)


def judge_answer(question: str, answer: str, expected_behavior: str = "", context: str = "") -> dict:
    parts = [f"问题: {question}", f"期望行为: {expected_behavior or '(未提供)'}"]
    if context:
        parts.append(f"工具调用结果(可用于核验回答中的数字):\n{context[:3000]}")
    parts.append(f"回答: {answer}")
    user = "\n".join(parts)
    try:
        result = chat_json(_RUBRIC, user)
    except LLMError as exc:
        raise JudgeError(str(exc)) from exc
    score = int(result.get("score", 1))
    score = max(1, min(5, score))
    return {
        "score": score,
        "reason": str(result.get("reason", "")),
        "issues": result.get("issues", []),
    }