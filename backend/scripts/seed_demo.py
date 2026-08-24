"""演示种子脚本:注册平台 Agent、创建评测数据集与 3 个演示用例。

用法:
  python scripts/seed_demo.py --platform-url http://127.0.0.1:8000

如需接入真实数据分析 Agent,先在其 backend/.env 设置:
  QC_TRACE_URL=http://127.0.0.1:8000/api/v1/traces/ingest
  QC_TRACE_AGENT_ID=<seed 输出的 agent_id>
  QC_TRACE_AGENT_KEY=<seed 输出的 api_key>
"""
import argparse

import httpx


DEMO_CASES = [
    {
        "input_prompt": "本月销售额下降的原因是什么?",
        "expected_behavior": "调用数据查询工具,结论中的数字必须与工具结果一致",
        "checks": [
            {"type": "tool_called", "tool": "query_sql"},
            {"type": "contains", "value": "下降"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "按品类画柱状图",
        "expected_behavior": "必须调用图表工具并返回图表描述",
        "checks": [
            {"type": "tool_called", "tool": "generate_chart"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "退款率怎么算?",
        "expected_behavior": "回答与知识库口径一致,包含退款分子分母定义",
        "checks": [
            {"type": "contains", "value": "退款"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "各渠道的销售额对比一下",
        "expected_behavior": "按渠道分组聚合销售额并对比",
        "checks": [
            {"type": "tool_called", "tool": "group_aggregate"},
            {"type": "contains", "value": "自营"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "哪个品类销售额最高?",
        "expected_behavior": "按品类聚合后给出最高品类",
        "checks": [
            {"type": "tool_called", "tool": "group_aggregate"},
            {"type": "contains", "value": "数码"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "6月和7月的销售额相比变化如何?",
        "expected_behavior": "对比两个月销售额并给出变化",
        "checks": [
            {"type": "tool_called", "tool": "query_sql"},
            {"type": "contains", "value": "下降"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "订单量最多的日期是哪天?",
        "expected_behavior": "查询订单量并找出最多的日期",
        "checks": [
            {"type": "tool_called", "tool": "query_sql"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "按日期画折线图看销售趋势",
        "expected_behavior": "调用图表工具展示销售趋势",
        "checks": [
            {"type": "tool_called", "tool": "generate_chart"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "客单价怎么计算?",
        "expected_behavior": "给出客单价定义与计算口径",
        "checks": [
            {"type": "contains", "value": "客单"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "毛利和毛利率怎么算?",
        "expected_behavior": "给出毛利与毛利率的定义和公式",
        "checks": [
            {"type": "contains", "value": "毛利"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "复购率怎么定义?怎么提升复购?",
        "expected_behavior": "给出复购率口径与提升方法",
        "checks": [
            {"type": "contains", "value": "复购"},
            {"type": "judge"},
        ],
    },
    {
        "input_prompt": "这份数据的数据质量怎么样?",
        "expected_behavior": "调用数据质量工具并给出结论",
        "checks": [
            {"type": "tool_called", "tool": "data_quality_report"},
            {"type": "contains", "value": "质量"},
            {"type": "judge"},
        ],
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform-url", default="http://127.0.0.1:8000")
    parser.add_argument("--sut-mcp-url", default="http://127.0.0.1:8000/mcp")
    args = parser.parse_args()

    base = args.platform_url.rstrip("/")
    # 本地直连:不读终端代理环境变量,避免 localhost 被代理劫持返回空响应
    client = httpx.Client(trust_env=False, timeout=30)

    agent = client.post(
        f"{base}/api/v1/agents/register",
        json={"name": "data-analysis-agent", "mcp_url": args.sut_mcp_url, "rate_limit_qps": 5},
    ).json()
    print(f"Agent 已注册: id={agent['id']}")
    print(f"API Key(保存好): {agent['api_key']}")
    print(f"MCP URL: {agent['mcp_url']}")

    try:
        tools = client.post(f"{base}/api/v1/agents/{agent['id']}/tools/sync").json()
        print(f"工具同步完成: {[t['name'] for t in tools]}")
    except Exception as exc:
        print(f"工具同步失败(SUT 未启动时可忽略): {exc}")

    dataset = client.post(
        f"{base}/api/v1/datasets",
        json={"name": "数据分析 Agent 演示集", "description": "3 个代表性业务场景"},
    ).json()
    for case in DEMO_CASES:
        resp = client.post(f"{base}/api/v1/datasets/{dataset['id']}/cases", json=case)
        resp.raise_for_status()
    print(f"评测数据集已创建: id={dataset['id']}，用例数={len(DEMO_CASES)}")
    print("下一步: 前端打开 http://localhost:5173 → 评测页 → 选择数据集执行。")
    client.close()


if __name__ == "__main__":
    main()