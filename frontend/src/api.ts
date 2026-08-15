import type {
  Agent,
  AgentRegistered,
  Dataset,
  EvalCase,
  MetricsOverview,
  Regression,
  ReviewItem,
  Run,
  RunDetail,
  Tool,
  Trace,
  TrendPoint,
} from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`${resp.status}: ${body.slice(0, 200)}`);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  registerAgent: (name: string, mcpUrl: string, rateLimitQps: number) =>
    request<AgentRegistered>("/api/v1/agents/register", {
      method: "POST",
      body: JSON.stringify({ name, mcp_url: mcpUrl, rate_limit_qps: rateLimitQps }),
    }),
  listAgents: () => request<Agent[]>("/api/v1/agents"),
  syncTools: (agentId: string) => request<Tool[]>(`/api/v1/agents/${agentId}/tools/sync`, { method: "POST" }),
  listTraces: (sessionId?: string, status?: string) =>
    request<Trace[]>(`/api/v1/traces?${new URLSearchParams({ ...(sessionId ? { session_id: sessionId } : {}), ...(status ? { status } : {}) })}`),
  getTrace: (traceId: string) => request<Trace>(`/api/v1/traces/${traceId}`),
  listDatasets: () => request<Dataset[]>("/api/v1/datasets"),
  createDataset: (name: string, description: string) =>
    request<Dataset>("/api/v1/datasets", { method: "POST", body: JSON.stringify({ name, description }) }),
  listCases: (datasetId: string) => request<EvalCase[]>(`/api/v1/datasets/${datasetId}/cases`),
  addCase: (datasetId: string, inputPrompt: string, checks: Record<string, unknown>[]) =>
    request<EvalCase>(`/api/v1/datasets/${datasetId}/cases`, {
      method: "POST",
      body: JSON.stringify({ input_prompt: inputPrompt, checks }),
    }),
  createRun: (datasetId: string, agentVersion: string) =>
    request<Run>("/api/v1/runs", { method: "POST", body: JSON.stringify({ dataset_id: datasetId, agent_version: agentVersion }) }),
  executeRun: (runId: string) => request<Run>(`/api/v1/runs/${runId}/execute`, { method: "POST" }),
  getRun: (runId: string) => request<RunDetail>(`/api/v1/runs/${runId}`),
  regression: (runId: string, baseline: string) =>
    request<Regression>(`/api/v1/runs/${runId}/regression?baseline=${baseline}`),
  overview: () => request<MetricsOverview>("/api/v1/metrics/overview"),
  trend: () => request<TrendPoint[]>("/api/v1/metrics/trend"),
  reviewQueue: (status?: string) =>
    request<ReviewItem[]>(`/api/v1/review-queue${status ? `?status=${status}` : ""}`),
  enqueueReview: (traceId: string) =>
    request<ReviewItem>("/api/v1/review-queue/items", { method: "POST", body: JSON.stringify({ trace_id: traceId }) }),
  decideReview: (itemId: number, status: string, note: string, promoteToDatasetId?: string, inputPrompt?: string) =>
    request<ReviewItem>(`/api/v1/review-queue/${itemId}/decide`, {
      method: "POST",
      body: JSON.stringify({
        status,
        note,
        ...(promoteToDatasetId ? { promote_to_dataset_id: promoteToDatasetId } : {}),
        ...(inputPrompt ? { input_prompt: inputPrompt } : {}),
      }),
    }),
};