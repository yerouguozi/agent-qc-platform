import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";
import { api } from "../api";
import type { MetricsOverview, TrendPoint } from "../types";

export default function DashboardPanel() {
  const [overview, setOverview] = useState<MetricsOverview | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.overview().then(setOverview).catch(console.error);
    api.trend().then((points) => {
      if (!chartRef.current) return;
      const chart = echarts.init(chartRef.current);
      chart.setOption({
        tooltip: { trigger: "axis" },
        legend: { data: ["通过率", "平均分"] },
        xAxis: { type: "category", data: points.map((p: TrendPoint) => p.day) },
        yAxis: { type: "value", max: 1 },
        series: [
          { name: "通过率", type: "line", data: points.map((p) => p.pass_rate), smooth: true },
          { name: "平均分", type: "line", data: points.map((p) => p.avg_score), smooth: true },
        ],
      });
    }).catch(console.error);
  }, []);

  if (!overview) return <div className="card">加载中…</div>;
  return (
    <div>
      <div className="grid">
        <div className="stat"><div className="num">{overview.trace_total}</div><div className="label">Trace 总数</div></div>
        <div className="stat"><div className="num">{(overview.success_rate * 100).toFixed(1)}%</div><div className="label">成功率</div></div>
        <div className="stat"><div className="num">{overview.avg_latency_ms}ms</div><div className="label">平均延迟</div></div>
        <div className="stat"><div className="num">${overview.total_cost.toFixed(4)}</div><div className="label">累计成本</div></div>
        <div className="stat"><div className="num">{overview.last_run_pass_rate === null ? "-" : `${(overview.last_run_pass_rate * 100).toFixed(0)}%`}</div><div className="label">最近一次评测通过率</div></div>
      </div>
      <div className="card"><div id="chart" ref={chartRef} /></div>
    </div>
  );
}