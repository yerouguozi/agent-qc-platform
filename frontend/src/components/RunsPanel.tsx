import { useEffect, useState } from "react";
import { api } from "../api";
import type { Dataset, RunDetail } from "../types";

export default function RunsPanel() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [dsName, setDsName] = useState("");
  const [dsDesc, setDsDesc] = useState("");
  const [prompt, setPrompt] = useState("");
  const [checksJson, setChecksJson] = useState('[{"type":"contains","value":"正确"}]');
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [version, setVersion] = useState("v1");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setError(null);
      setDatasets(await api.listDatasets());
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
    } catch (e) {
      setError(String(e));
    }
  };

  const createAndRun = async (datasetId: string) => {
    setRunning(true);
    setError(null);
    try {
      const run = await api.createRun(datasetId, version);
      const done = await api.executeRun(run.id);
      setDetail(await api.getRun(done.id));
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  };

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
          <h3>{ds.name}（{ds.id.slice(0, 8)}）</h3>
          <div className="row">
            <input placeholder="输入 prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
            <input placeholder="checks JSON" value={checksJson} onChange={(e) => setChecksJson(e.target.value)} />
            <button className="btn ghost" onClick={() => addCase(ds.id)}>添加用例</button>
          </div>
          <div className="row" style={{ marginTop: 10 }}>
            <input placeholder="Agent 版本，如 v1" value={version} onChange={(e) => setVersion(e.target.value)} disabled={running} />
            <button className="btn" onClick={() => createAndRun(ds.id)} disabled={running}>
              {running ? "评测中…（1-2 分钟）" : "创建并执行评测"}
            </button>
          </div>
        </div>
      ))}
      {running && <div className="card">⏳ 评测执行中，请稍候…正在跑 3 个真实业务场景</div>}
      {detail && (
        <div className="card">
          <h3>运行结果 {detail.id.slice(0, 8)}（{detail.agent_version}）</h3>
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
        </div>
      )}
    </div>
  );
}