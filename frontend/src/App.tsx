import { useState } from "react";
import AgentsPanel from "./components/AgentsPanel";
import DashboardPanel from "./components/DashboardPanel";
import ReviewQueue from "./components/ReviewQueue";
import RunsPanel from "./components/RunsPanel";
import TracesPanel from "./components/TracesPanel";

const TABS = ["总览", "Agents", "Traces", "评测", "复核"] as const;
type Tab = (typeof TABS)[number];

export default function App() {
  const [tab, setTab] = useState<Tab>("总览");
  return (
    <div>
      <nav className="nav">
        {TABS.map((t) => (
          <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </nav>
      <div className="page">
        {tab === "总览" && <DashboardPanel />}
        {tab === "Agents" && <AgentsPanel />}
        {tab === "Traces" && <TracesPanel />}
        {tab === "评测" && <RunsPanel />}
        {tab === "复核" && <ReviewQueue />}
      </div>
    </div>
  );
}