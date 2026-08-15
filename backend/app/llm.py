import json
import time

import httpx

from app.core.config import settings


class LLMError(Exception):
    pass


def chat_json(
    system: str,
    user: str,
    *,
    timeout: float | None = None,
    max_retries: int | None = None,
) -> dict:
    if not settings.deepseek_api_key:
        raise LLMError("DEEPSEEK_API_KEY 未配置")
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": settings.model_name,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    timeout = settings.judge_timeout if timeout is None else timeout
    max_retries = settings.judge_max_retries if max_retries is None else max_retries
    last_exc: Exception | None = None
    with httpx.Client(timeout=timeout) as client:
        for attempt in range(max_retries + 1):
            try:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    return parsed
                raise LLMError(f"非 JSON 对象输出: {content[:200]}")
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
    raise LLMError(f"LLM 调用失败: {last_exc}")