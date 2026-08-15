import { useEffect, useState } from "react";
import { api } from "../api";
import type { Trace } from "../types";

export default function TracesPanel() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<Trace | null>(null);

  const load = () => api.listTraces(sessionId || undefined, status || undefined).then(setTraces).catch(console.error);
  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="card row">
        <input placeholder="会话 ID（可选）" value={sessionId} onChange={(e) => setSessionId(e.target.value)} />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">全部状态</option>
          <option value="success">success</option>
          <option value="failed">failed</option>
          <option value="timeout">timeout</option>
          <option value="ratelimited">ratelimited</option>
        </select>
        <button className="btn" onClick={load}>查询</button>
      </div>
      <div className="card">
        <table>
          <thead><tr><th>时间</th><th>工具</th><th>会话</th><th>状态</th><th>延迟</th><th>成本</th><th></th></tr></thead>
          <tbody>
            {traces.map((t) => (
              <tr key={t.id}>
                <td>{t.created_at}</td>
                <td>{t.tool_name}</td>
                <td>{t.session_id}</td>
                <td><span className={`badge ${t.status === "success" ? "ok" : "bad"}`}>{t.status}</span></td>
                <td>{t.latency_ms}ms</td>
                <td>{t.cost}</td>
                <td><button className="btn ghost" onClick={() => setSelected(t)}>详情</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected && (
        <div className="card">
          <h3>Trace 详情 {selected.trace_id}</h3>
          <pre>{JSON.stringify(selected, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}