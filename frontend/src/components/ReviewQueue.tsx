import { useEffect, useState } from "react";
import { api } from "../api";
import type { Dataset, ReviewItem, Trace } from "../types";

export default function ReviewQueue() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [traceId, setTraceId] = useState("");

  const refresh = () => {
    api.reviewQueue().then(setItems).catch(console.error);
    api.listDatasets().then(setDatasets).catch(console.error);
    api.listTraces().then(setTraces).catch(console.error);
  };
  useEffect(() => { refresh(); }, []);

  const enqueue = async () => {
    if (!traceId) return;
    try {
      await api.enqueueReview(traceId);
      setTraceId("");
      refresh();
    } catch (e) {
      alert(String(e));
    }
  };

  const decide = async (itemId: number, status: string) => {
    const target = items.find((i) => i.id === itemId);
    if (status === "rejected" && target) {
      const dsId = prompt("沉淀到哪个数据集 ID？（在评测页创建）") || "";
      const inputPrompt = prompt("复现问题的输入 prompt：") || "";
      if (dsId && inputPrompt) {
        await api.decideReview(itemId, "rejected", "驳回并沉淀", dsId, inputPrompt);
      } else {
        return;
      }
    } else {
      await api.decideReview(itemId, status, "approved");
    }
    refresh();
  };

  return (
    <div>
      <div className="card row">
        <select value={traceId} onChange={(e) => setTraceId(e.target.value)}>
          <option value="">选择要复核的 trace…</option>
          {traces.map((t) => (
            <option key={t.trace_id} value={t.trace_id}>
              {t.tool_name} · {t.status} · {t.trace_id.slice(0, 12)}…
            </option>
          ))}
        </select>
        <button className="btn" onClick={enqueue} disabled={!traceId}>加入复核队列</button>
      </div>
      <div className="card">
        <h3>复核队列</h3>
        <table>
          <thead><tr><th>Trace</th><th>状态</th><th>备注</th><th></th></tr></thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id}>
                <td>{i.trace_id}</td>
                <td>{i.status}</td>
                <td>{i.reviewer_note || "-"}</td>
                <td>
                  {i.status === "pending" && (
                    <div className="row">
                      <button className="btn ghost" onClick={() => decide(i.id, "approved")}>通过</button>
                      <button className="btn" onClick={() => decide(i.id, "rejected")}>驳回并沉淀</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="card">
        <h3>可用数据集（沉淀目标）</h3>
        {datasets.map((d) => <div key={d.id}>{d.name}（{d.id}）</div>)}
      </div>
    </div>
  );
}