import { useEffect, useState } from "react";
import { api } from "../api";
import type { Dataset, Run, RunDetail } from "../types";

export default function RunsPanel() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [dsName, setDsName] = useState("");
  const [dsDesc, setDsDesc] = useState("");
  const [prompt, setPrompt] = useState("");
  const [checksJson, setChecksJson] = useState('[{"type":"contains","value":"正确"}]');
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [version, setVersion] = useState("v1");

  const refresh = () => api.listDatasets().then(setDatasets).catch(console.error);
  useEffect(() => { refresh(); }, []);

  const createDataset = async () => {
    const ds = await api.createDataset(dsName, dsDesc);
    setDsName("");
    setDsDesc("");
    refresh();
  };

  const addCase = async (datasetId: string) => {
    let checks: Record<string, unknown>[];
    try {
      checks = JSON.parse(checksJson);
    } catch {
      alert("checks JSON 不合法");
      return;
    }
    await api.addCase(datasetId, prompt, checks);
    setPrompt("");
  };

  const createAndRun = async (datasetId: string) => {
    const run = await api.createRun(datasetId, version);
    const done = await api.executeRun(run.id);
    setDetail(await api.getRun(done.id));
  };

  return (
    <div>
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
            <input placeholder="Agent 版本，如 v1" value={version} onChange={(e) => setVersion(e.target.value)} />
            <button className="btn" onClick={() => createAndRun(ds.id)}>创建并执行评测</button>
          </div>
        </div>
      ))}
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