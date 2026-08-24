import json
import re


class CaseOutput:
    def __init__(self, answer: str, tool_calls: list[str] | None = None, trace_id: str | None = None, trace_summaries: list[str] | None = None):
        self.answer = answer
        self.tool_calls = tool_calls or []
        self.trace_id = trace_id
        self.trace_summaries = trace_summaries or []


def _resolve_path(data, path: str):
    node = data
    for part in path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            return None
    return node


def run_check(check: dict, output: CaseOutput) -> tuple[bool, str]:
    ctype = check.get("type")
    if ctype == "exact":
        return output.answer.strip() == str(check.get("value", "")), f"exact 期望={check.get('value')!r}"
    if ctype == "contains":
        return str(check.get("value", "")) in output.answer, f"contains 期望包含={check.get('value')!r}"
    if ctype == "regex":
        try:
            return re.search(str(check.get("pattern", "")), output.answer) is not None, f"regex={check.get('pattern')}"
        except re.error as exc:
            return False, f"regex 非法:{exc}"
    if ctype == "numeric_range":
        match = re.search(r"-?\d+(?:\.\d+)?", output.answer)
        if not match:
            return False, "numeric_range 未找到数字"
        value = float(match.group(0))
        lo = check.get("min")
        hi = check.get("max")
        ok = (lo is None or value >= lo) and (hi is None or value <= hi)
        return ok, f"numeric_range 值={value}"
    if ctype == "tool_called":
        tool = str(check.get("tool", ""))
        return tool in output.tool_calls, f"tool_called 期望={tool} 实际={output.tool_calls}"
    if ctype == "not_tool_called":
        tool = str(check.get("tool", ""))
        return tool not in output.tool_calls, f"not_tool_called 禁止={tool} 实际={output.tool_calls}"
    if ctype == "json_path":
        try:
            data = json.loads(output.answer)
        except json.JSONDecodeError:
            return False, "json_path 答案不是合法 JSON"
        value = _resolve_path(data, str(check.get("path", "")))
        expected = check.get("value")
        op = check.get("op", "eq")
        if op == "eq":
            return value == expected, f"json_path {check.get('path')}={value!r}"
        if op == "contains":
            return expected in value if isinstance(value, (list, str, dict)) else False, "json_path contains"
        return False, f"未知 op={op}"
    return False, f"未知检查类型={ctype}"


def run_checks(checks: list[dict], output: CaseOutput) -> tuple[bool, list[dict]]:
    details = []
    for check in checks:
        if check.get("type") == "judge":
            continue
        passed, message = run_check(check, output)
        details.append({"check": check, "passed": passed, "message": message})
    return all(d["passed"] for d in details), details