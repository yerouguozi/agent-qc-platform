export interface Agent {
  id: string;
  name: string;
  mcp_url: string;
  rate_limit_qps: number;
  status: string;
  created_at: string;
}

export interface AgentRegistered extends Agent {
  api_key: string;
}

export interface Tool {
  id: string;
  agent_id: string;
  name: string;
  description: string;
  status: string;
}

export interface Trace {
  id: number;
  trace_id: string;
  session_id: string;
  agent_id: string;
  tool_name: string;
  params_masked_json: string;
  result_summary: string;
  status: string;
  latency_ms: number;
  token_usage: number;
  cost: number;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
}

export interface Dataset {
  id: string;
  name: string;
  description: string;
  created_at: string;
}

export interface EvalCase {
  id: string;
  dataset_id: string;
  input_prompt: string;
  expected_behavior: string;
  checks: Record<string, unknown>[];
  source_trace_id: string | null;
  created_at: string;
}

export interface Run {
  id: string;
  dataset_id: string;
  agent_version: string;
  agent_id: string | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  summary_json: string | null;
}

export interface CaseResult {
  case_id: string;
  input_prompt: string;
  deterministic_pass: boolean;
  judge_score: number | null;
  judge_reason: string | null;
  judge_degraded: boolean;
  overall_pass: boolean;
}

export interface RunDetail extends Run {
  results: CaseResult[];
}

export interface MetricsOverview {
  trace_total: number;
  success_rate: number;
  avg_latency_ms: number;
  total_cost: number;
  last_run_pass_rate: number | null;
}

export interface TrendPoint {
  day: string;
  pass_rate: number | null;
  avg_score: number | null;
}

export interface ReviewItem {
  id: number;
  trace_id: string;
  status: string;
  reviewer_note: string | null;
  created_at: string;
  decided_at: string | null;
}

export interface RegressionRow {
  case_id: string;
  input_prompt: string;
  baseline_pass: boolean | null;
  current_pass: boolean | null;
  baseline_score: number | null;
  current_score: number | null;
}

export interface Regression {
  baseline_run_id: string;
  current_run_id: string;
  pass_rate_baseline: number;
  pass_rate_current: number;
  avg_score_baseline: number | null;
  avg_score_current: number | null;
  new_failures: string[];
  rows: RegressionRow[];
}