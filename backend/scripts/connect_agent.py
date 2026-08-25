"""通用 Agent 接入脚本:注册平台 Agent + 建评测数据集 + 加用例。

用法:
  python scripts/connect_agent.py --name "客服Agent" --chat-url http://127.0.0.1:8002 \
      --driver-type customer_service --dataset "客服评测集" --cases scripts/cases_cs.json

流程:在 SUT 注册/登录用户拿 token -> 平台注册 Agent(带 chat 配置) -> 建数据集并加用例。
"""
import argparse
import json
import sys
from pathlib import Path

import httpx

PLATFORM = "http://127.0.0.1:8000"


def _sut_ready(client: httpx.Client) -> None:
    """SUT 健康探测:兼容 /health 与 /api/health。"""
    for path in ("/health", "/api/health", "/docs"):
        try:
            r = client.get(path)
            if r.status_code < 500:
                return
        except Exception:
            continue
    raise RuntimeError("SUT 健康检查失败")


def get_sut_token(client: httpx.Client, username: str, password: str) -> str:
    body = {"username": username, "password": password}
    r = client.post("/api/auth/register", json=body)
    if r.status_code >= 400:
        r = client.post("/api/auth/login", json=body)
    r.raise_for_status()
    data = r.json()
    return data.get("access_token") or data.get("token")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--chat-url", required=True)
    parser.add_argument("--driver-type", default="http")
    parser.add_argument("--username", default="demo")
    parser.add_argument("--password", default="demo123")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--cases", default="", help="用例 JSON 文件路径")
    parser.add_argument("--platform", default=PLATFORM)
    args = parser.parse_args()

    platform = httpx.Client(base_url=args.platform, trust_env=False, timeout=30)
    sut = httpx.Client(base_url=args.chat_url, trust_env=False, timeout=30)
    try:
        platform.get("/health").raise_for_status()
        _sut_ready(sut)
    except Exception:
        print("请先启动平台后端与 SUT 后端")
        sys.exit(1)

    token = get_sut_token(sut, args.username, args.password)

    reg = platform.post(
        "/api/v1/agents/register",
        json={
            "name": args.name,
            "mcp_url": args.chat_url + "/mcp",
            "rate_limit_qps": 5,
            "chat_url": args.chat_url,
            "auth_token": token,
            "driver_type": args.driver_type,
        },
    ).json()
    print(f"Agent 已注册: id={reg['id']} driver_type={args.driver_type}")

    ds = platform.post("/api/v1/datasets", json={"name": args.dataset, "description": args.name}).json()
    print(f"数据集已创建: id={ds['id']}")

    if args.cases:
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
        for case in cases:
            r = platform.post(f"/api/v1/datasets/{ds['id']}/cases", json=case)
            r.raise_for_status()
        print(f"已添加 {len(cases)} 个用例")

    print("完成: 前端评测页刷新后,Agent 下拉选择该 Agent 即可评测。")


if __name__ == "__main__":
    main()