import { useEffect, useState } from "react";
import { api } from "../api";
import type { Agent, AgentRegistered, Tool } from "../types";

export default function AgentsPanel() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [name, setName] = useState("");
  const [mcpUrl, setMcpUrl] = useState("");
  const [qps, setQps] = useState(5);
  const [registered, setRegistered] = useState<AgentRegistered | null>(null);
  const [tools, setTools] = useState<Record<string, Tool[]>>({});

  const refresh = () => api.listAgents().then(setAgents).catch(console.error);
  useEffect(() => { refresh(); }, []);

  const register = async () => {
    const agent = await api.registerAgent(name, mcpUrl, qps);
    setRegistered(agent);
    setName("");
    setMcpUrl("");
    refresh();
  };

  const sync = async (agentId: string) => {
    const rows = await api.syncTools(agentId);
    setTools((prev) => ({ ...prev, [agentId]: rows }));
  };

  return (
    <div>
      <div className="card">
        <h3>注册 Agent</h3>
        <input placeholder="名称" value={name} onChange={(e) => setName(e.target.value)} />
        <input placeholder="MCP URL，如 http://127.0.0.1:8000/mcp" value={mcpUrl} onChange={(e) => setMcpUrl(e.target.value)} />
        <input type="number" placeholder="QPS" value={qps} onChange={(e) => setQps(Number(e.target.value))} />
        <button className="btn" onClick={register}>注册</button>
        {registered && (
          <pre>API Key（只显示一次，请保存）：{registered.api_key}</pre>
        )}
      </div>
      <div className="card">
        <h3>Agent 列表</h3>
        <table>
          <thead><tr><th>名称</th><th>MCP URL</th><th>QPS</th><th>状态</th><th>工具</th></tr></thead>
          <tbody>
            {agents.map((a) => (
              <tr key={a.id}>
                <td>{a.name}</td>
                <td>{a.mcp_url}</td>
                <td>{a.rate_limit_qps}</td>
                <td>{a.status}</td>
                <td>
                  <button className="btn ghost" onClick={() => sync(a.id)}>同步工具</button>
                  {tools[a.id]?.map((t) => <div key={t.id}>{t.name}</div>)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}