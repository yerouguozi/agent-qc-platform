from app.eval.checks import CaseOutput, run_check, run_checks


def output(answer="", tool_calls=None):
    return CaseOutput(answer=answer, tool_calls=tool_calls or [])


def test_exact_and_contains():
    assert run_check({"type": "exact", "value": "42"}, output("42"))[0]
    assert not run_check({"type": "exact", "value": "42"}, output("43"))[0]
    assert run_check({"type": "contains", "value": "退款"}, output("退款率按 X 计算"))[0]


def test_regex_and_numeric_range():
    assert run_check({"type": "regex", "pattern": r"\d+%"}, output("转化率 12.5%"))[0]
    passed, _ = run_check({"type": "numeric_range", "min": 10, "max": 20}, output("下降 15%"))
    assert passed


def test_tool_checks():
    out = output(tool_calls=["load_dataset", "query_sql"])
    assert run_check({"type": "tool_called", "tool": "query_sql"}, out)[0]
    assert run_check({"type": "not_tool_called", "tool": "delete_dataset"}, out)[0]
    assert not run_check({"type": "tool_called", "tool": "chart"}, out)[0]


def test_json_path_check():
    out = output('{"sales": {"q1": 100}}')
    assert run_check({"type": "json_path", "path": "sales.q1", "op": "eq", "value": 100}, out)[0]


def test_unknown_check_fails():
    assert not run_check({"type": "nope"}, output())[0]


def test_run_checks_skips_judge():
    checks = [{"type": "contains", "value": "ok"}, {"type": "judge"}]
    passed, details = run_checks(checks, output("ok"))
    assert passed
    assert len(details) == 1