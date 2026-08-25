"""一键端到端演示:自动完成 注册Agent/插桩配置/SUT配置/数据上传/建用例/跑评测。

前提:旧Agent(8001)与平台后端(8000)都已启动。
用法: python scripts/e2e_demo.py
首次运行会写入两处配置并提示重启;之后直接出结果,无需复制任何值。
"""
import json
import re
import sys
import time
from pathlib import Path

import httpx

PLATFORM = "http://127.0.0.1:8000"
SUT = "http://127.0.0.1:8001"
BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_DIR / ".env"
QC_STATE = BACKEND_DIR / ".qc_agent.json"
OLD_ENV = Path(r"C:\Users\huiyi\project_agent\data-analysis-agent-team\backend\.env")
SALES = BACKEND_DIR / "sample_data" / "sales.csv"
DEMO_NAME = "数据分析 Agent 演示集"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_demo import DEMO_CASES  # noqa: E402


def ensure_sut_user(client: httpx.Client) -> str:
    body = {"username": "demo", "password": "demo123"}
    r = client.post("/api/auth/register", json=body)
    if r.status_code >= 400:
        r = client.post("/api/auth/login", json=body)
    r.raise_for_status()
    return r.json()["token"]


def ensure_sut_dataset(client: httpx.Client, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    for d in client.get("/api/datasets", headers=headers).json():
        if d.get("filename") == "sales.csv":
            return d["id"]
    with SALES.open("rb") as f:
        up = client.post("/api/datasets", headers=headers, files={"file": ("sales.csv", f, "text/csv")})
    up.raise_for_status()
    return up.json()["id"]


def ensure_platform_env(token: str, dsid: str) -> bool:
    """更新平台 .env 的 SUT 配置,返回是否需要重启后端。"""
    text = ENV_PATH.read_text(encoding="utf-8")
    new = re.sub(r"(?m)^SUT_CHAT_URL=.*$", "SUT_CHAT_URL=" + SUT, text)
    new = re.sub(r"(?m)^SUT_AUTH_TOKEN=.*$", "SUT_AUTH_TOKEN=" + token, new)
    new = re.sub(r"(?m)^SUT_DATASET_ID=.*$", "SUT_DATASET_ID=" + dsid, new)
    changed = new != text
    if changed:
        ENV_PATH.write_text(new, encoding="utf-8")
    return changed


def ensure_platform_agent(client: httpx.Client, token: str, dsid: str) -> tuple[dict, bool]:
    """注册(或复用)带 SUT 配置的平台 Agent;返回 (state, 是否新注册)。"""
    if QC_STATE.exists():
        st = json.loads(QC_STATE.read_text(encoding="utf-8"))
        by_id = {a["id"]: a for a in client.get("/api/v1/agents").json()}
        cur = by_id.get(st["id"])
        if cur is not None and cur.get("chat_url") == SUT and cur.get("dataset_id") == dsid:
            return st, False
    reg = client.post(
        "/api/v1/agents/register",
        json={
            "name": "data-analysis-agent",
            "mcp_url": SUT + "/mcp",
            "rate_limit_qps": 5,
            "chat_url": SUT,
            "auth_token": token,
            "dataset_id": dsid,
        },
    ).json()
    st = {"id": reg["id"], "key": reg["api_key"]}
    QC_STATE.write_text(json.dumps(st), encoding="utf-8")
    return st, True


def ensure_old_env_qc(st: dict) -> bool:
    """把插桩配置写进旧 Agent 的 .env,返回是否需要重启旧 Agent。"""
    text = OLD_ENV.read_text(encoding="utf-8")
    url_line = f"QC_TRACE_URL={PLATFORM}/api/v1/traces/ingest"
    id_line = f"QC_TRACE_AGENT_ID={st['id']}"
    key_line = f"QC_TRACE_AGENT_KEY={st['key']}"
    new = re.sub(r"(?m)^QC_TRACE_URL=.*$", url_line, text)
    new = re.sub(r"(?m)^QC_TRACE_AGENT_ID=.*$", id_line, new)
    new = re.sub(r"(?m)^QC_TRACE_AGENT_KEY=.*$", key_line, new)
    for line in (url_line, id_line, key_line):
        if line.split("=")[0] not in new:
            new += "\n" + line
    changed = new != text
    if changed:
        OLD_ENV.write_text(new, encoding="utf-8")
    return changed


def ensure_gitignore() -> None:
    gi = BACKEND_DIR.parent / ".gitignore"
    text = gi.read_text(encoding="utf-8")
    if ".qc_agent.json" not in text:
        gi.write_text(text.rstrip() + "\n.qc_agent.json\n", encoding="utf-8")


def ensure_platform_dataset(client: httpx.Client) -> str:
    for d in client.get("/api/v1/datasets").json():
        if d["name"] == DEMO_NAME:
            return d["id"]
    ds = client.post("/api/v1/datasets", json={"name": DEMO_NAME, "description": "端到端演示"}).json()
    for case in DEMO_CASES:
        r = client.post(f"/api/v1/datasets/{ds['id']}/cases", json=case)
        r.raise_for_status()
    return ds["id"]


def run_eval(client: httpx.Client, dsid: str, agent_id: str) -> None:
    run = client.post(
        "/api/v1/runs",
        json={"dataset_id": dsid, "agent_version": "v1", "agent_id": agent_id},
    ).json()
    client.post(f"/api/v1/runs/{run['id']}/execute")
    while True:
        time.sleep(2)
        detail = client.get(f"/api/v1/runs/{run['id']}").json()
        if detail["status"] in ("completed", "failed"):
            break
    passed = sum(1 for r in detail["results"] if r["overall_pass"])
    total = len(detail["results"])
    print(f"\n=== 运行 {run['id'][:8]} · {detail['status']} · 通过率 {passed}/{total} ===")
    for r in detail["results"]:
        mark = "✅" if r["overall_pass"] else "❌"
        print(f"{mark} [{r['judge_score'] if r['judge_score'] is not None else '-'}] {r['input_prompt']}")


def main() -> None:
    try:
        platform = httpx.Client(base_url=PLATFORM, trust_env=False, timeout=30)
        sut = httpx.Client(base_url=SUT, trust_env=False, timeout=120)
        platform.get("/health").raise_for_status()
        sut.get("/health").raise_for_status()
    except Exception:
        print("请先启动两个后端:平台 8000 与旧 Agent 8001")
        sys.exit(1)

    ensure_gitignore()
    token = ensure_sut_user(sut)
    dsid = ensure_sut_dataset(sut, token)
    env_changed = ensure_platform_env(token, dsid)
    agent, agent_new = ensure_platform_agent(platform, token, dsid)
    qc_changed = ensure_old_env_qc(agent) or agent_new

    if qc_changed or env_changed:
        print("配置已自动写入(平台 .env 与旧 Agent .env)。")
        print("请重启 平台8000 与 旧Agent8001,然后重新运行本脚本。")
        return

    pdsid = ensure_platform_dataset(platform)
    print("开始评测(12 个真实场景,约 2-4 分钟)...")
    run_eval(platform, pdsid, agent["id"])


if __name__ == "__main__":
    main()