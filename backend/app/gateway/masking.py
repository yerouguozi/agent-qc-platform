import re

_PATTERNS = [
    (re.compile(r"1[3-9]\d{9}"), lambda m: m.group(0)[:3] + "****" + m.group(0)[-4:]),
    (re.compile(r"\d{17}[\dXx]"), lambda m: m.group(0)[:6] + "**********" + m.group(0)[-4:]),
    (re.compile(r"\d{6,}"), lambda m: m.group(0)[:2] + "****" + m.group(0)[-2:]),
]


def mask_text(value: str) -> str:
    for pattern, repl in _PATTERNS:
        value = pattern.sub(repl, value)
    return value


def mask_value(value):
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, list):
        return [mask_value(v) for v in value]
    if isinstance(value, dict):
        return {k: mask_value(v) for k, v in value.items()}
    return value


def mask_arguments(arguments: dict) -> dict:
    return mask_value(arguments)