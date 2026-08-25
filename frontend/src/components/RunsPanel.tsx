import { useEffect, useState } from "react";
import { api } from "../api";
import type { Agent, Dataset, EvalCase, Regression, Run, RunDetail } from "../types";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export default function RunsPanel() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [casesMap, setCasesMap] = useState<Record<string, EvalCase[]>>({});
  const [dsName, setDsName] = useState("");
  const [dsDesc, setDsDesc] = useState("");
  const [prompt, setPrompt] = useState("");
  const [checksJson, setChecksJson] = useState('[{"type":"contains","value":"正确"}]');
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [version, setVersion] = useState("v1");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [baselineId, setBaselineId] = useState("");
  const [currentId, setCurrentId] = useState("");
  const [reg, setReg] = useState<Regression | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentId, setAgentId] = useState("");

  const refresh = async () => {
    try {
      setError(null);
      const [ds, rs, ags] = await Promise.all([api.listDatasets(), api.listRuns(), api.listAgents()]);
      setDatasets(ds);
      setRuns(rs);
      setAgents(ags);
      setAgentId((prev) => prev || (ags[0]?.id ?? ""));
      const map: Record<string, EvalCase[]> = {};
      await Promise.all(ds.map(async (d) => { map[d.id] = await api.listCases(d.id); }));
      setCasesMap(map);
    } catch (e) {
      setError(String(e));
    }
  };
  useEffect(() => { refresh(); }, []);

  const createDataset = async () => {
    try {
      setError(null);
      await api.createDataset(dsName, dsDesc);
      setDsName("");
      setDsDesc("");
      refresh();
    } catch (e) {
      setError(String(e));
    }
  };

  const addCase = async (datasetId: string) => {
    if (!prompt.trim()) return;
    let checks: Record<string, unknown>[];
    try {
      checks = JSON.parse(checksJson);
    } catch {
      setError("checks JSON 不合法");
      return;
    }
    try {
      setError(null);
      await api.addCase(datasetId, prompt, checks);
      setPrompt("");
      alert("已添加用例 ✅");
      refresh();
    } catch (e) {
      setError(String(e));
    }
  };

  const createAndRun = async (datasetId: string) => {
    setRunning(true);
    setError(null);
    try {
      const run = await api.createRun(datasetId, version, agentId || undefined);
      await api.executeRun(run.id);
      for (;;) {
        await sleep(2000);
        const d = await api.getRun(run.id);
        setDetail(d);
        if (d.status === "completed" || d.status === "failed") break;
      }
      refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  };

  const removeDataset = async (datasetId: string) => {
    if (!confirm("确认删除该数据集及其全部用例/运行?")) return;
    try {
      setError(null);
      await api.deleteDataset(datasetId);
      refresh();
    } catch (e) {
      setError(String(e));
    }
  };

  const removeCase = async (datasetId: string, caseId: string) => {
    if (!confirm("确认删除该用例?")) return;
    try {
      setError(null);
      await api.deleteCase(datasetId, caseId);
      refresh();
    } catch (e) {
      setError(String(e));
    }
  };

  const viewRun = async (runId: string) => {
    try {
      setError(null);
      setDetail(await api.getRun(runId));
    } catch (e) {
      setError(String(e));
    }
  };

  const compare = async () => {
    if (!baselineId || !currentId || baselineId === currentId) return;
    try {
      setError(null);
      setReg(await api.regression(currentId, baselineId));
    } catch (e) {
      setError(String(e));
    }
  };

  const progress = (() => {
    if (!detail || !detail.summary_json) return null;
    try {
      const s = JSON.parse(detail.summary_json);
      return { cases: s.cases ?? 0, done: s.done ?? 0 };
    } catch {
      return null;
    }
  })();

  return (
    <div>
      {error && <div className="card" style={{ borderColor: "#f53f3f", color: "#f53f3f" }}>出错了：{error}</div>}
      <div className="card">
        <h3>新建数据集</h3>
        <input placeholder="数据集名称" value={dsName} onChange={(e) => setDsName(e.target.value)} />
        <input placeholder="描述" value={dsDesc} onChange={(e) => setDsDesc(e.target.value)} />
        <button className="btn" onClick={createDataset}>创建</button>
      </div>
      {datasets.map((ds) => (
        <div className="card" key={ds.id}>
          <h3>
            {ds.name}（{ds.id.slice(0, 8)}）· 用例数：{(casesMap[ds.id] || []).length}
            <button className="btn ghost" style={{ marginLeft: 8, color: "#f53f3f" }} onClick={() => removeDataset(ds.id)}>删除</button>
          </h3>
          <div className="row">
            <input placeholder="输入 prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
            <input placeholder="checks JSON" value={checksJson} onChange={(e) => setChecksJson(e.target.value)} />
            <button className="btn ghost" onClick={() => addCase(ds.id)} disabled={!prompt.trim()}>添加用例</button>
          </div>
          {(casesMap[ds.id] || []).length > 0 && (
            <ul style={{ fontSize: 13, color: "#4e5969" }}>
              {(casesMap[ds.id] || []).map((c) => (
                <li key={c.id}>
                  {c.input_prompt.slice(0, 40)}
                  <button
                    style={{ marginLeft: 8, color: "#f53f3f", border: "none", background: "none", cursor: "pointer" }}
                    onClick={() => removeCase(ds.id, c.id)}
                  >✕</button>
                </li>
              ))}
            </ul>
          )}
          <div className="row" style={{ marginTop: 10 }}>
            <select value={agentId} onChange={(e) => setAgentId(e.target.value)} disabled={running}>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>{a.name}（{a.id.slice(0, 8)}）</option>
              ))}
            </select>
            <input placeholder="Agent 版本，如 v1" value={version} onChange={(e) => setVersion(e.target.value)} disabled={running} />
            <button className="btn" onClick={() => createAndRun(ds.id)} disabled={running}>
              {running ? "评测中…" : "创建并执行评测"}
            </button>
          </div>
        </div>
      ))}
      {running && (
        <div className="card">
          ⏳ 评测执行中{progress ? `（${progress.done}/${progress.cases} 个用例）` : ""}…
        </div>
      )}
      {detail && (
        <div className="card">
          <h3>运行结果 {detail.id.slice(0, 8)}（{detail.agent_version}）· {detail.status}</h3>
          {detail.status === "completed" ? (
            <table>
              <thead><tr><th>用例</th><th>确定性</th><th>Judge 分</th><th>总体</th></tr></thead>
              <tbody>
                {detail.results.map((r) => (
                  <tr key={r.case_id}>
                    <td>{r.input_prompt}</td>
                    <td>{r.deterministic_pass ? "通过" : "失败"}</td>
                    <td>{r.judge_score ?? "-"}</td>
                    <td><span className={`badge ${r.overall_pass ? "ok" : "bad"}`}>{r.overall_pass ? "通过" : "失败"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div>执行中，已出 {detail.results.length} 个结果…</div>
          )}
        </div>
      )}
      <div className="card">
        <h3>回归对比</h3>
        <div className="row">
          <select value={baselineId} onChange={(e) => setBaselineId(e.target.value)}>
            <option value="">基线版本（旧）</option>
            {runs.filter((r) => r.id !== currentId).map((r) => (
              <option key={r.id} value={r.id}>{r.id.slice(0, 8)} · {r.agent_version} · {r.status}</option>
            ))}
          </select>
          <select value={currentId} onChange={(e) => setCurrentId(e.target.value)}>
            <option value="">当前版本（新）</option>
            {runs.filter((r) => r.id !== baselineId).map((r) => (
              <option key={r.id} value={r.id}>{r.id.slice(0, 8)} · {r.agent_version} · {r.status}</option>
            ))}
          </select>
          <button className="btn" onClick={compare} disabled={!baselineId || !currentId || baselineId === currentId}>对比</button>
        </div>
        {reg && (
          <div style={{ marginTop: 10 }}>
            <p>
              通过率：<b>{Math.round(reg.pass_rate_baseline * 100)}%</b> → <b>{Math.round(reg.pass_rate_current * 100)}%</b>
              {" "}· 平均分：<b>{reg.avg_score_baseline ?? "-"}</b> → <b>{reg.avg_score_current ?? "-"}</b>
              {" "}· 新失败：<b>{reg.new_failures.length}</b>
            </p>
            <table>
              <thead><tr><th>用例</th><th>基线</th><th>当前</th><th>基线分</th><th>当前分</th></tr></thead>
              <tbody>
                {reg.rows.map((row) => (
                  <tr key={row.case_id}>
                    <td>{row.input_prompt}</td>
                    <td><span className={`badge ${row.baseline_pass ? "ok" : "bad"}`}>{row.baseline_pass === null ? "-" : row.baseline_pass ? "通过" : "失败"}</span></td>
                    <td><span className={`badge ${row.current_pass ? "ok" : "bad"}`}>{row.current_pass === null ? "-" : row.current_pass ? "通过" : "失败"}</span></td>
                    <td>{row.baseline_score ?? "-"}</td>
                    <td>{row.current_score ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <div className="card">
        <h3>历史运行</h3>
        <table>
          <thead><tr><th>运行</th><th>版本</th><th>状态</th><th>时间</th><th></th></tr></thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id}>
                <td>{r.id.slice(0, 8)}</td>
                <td>{r.agent_version}</td>
                <td>{r.status}</td>
                <td>{r.started_at}</td>
                <td><button className="btn ghost" onClick={() => viewRun(r.id)}>查看</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}