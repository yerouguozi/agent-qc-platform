from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str


class AgentRegisterIn(BaseModel):
    name: str
    mcp_url: str
    rate_limit_qps: int = 5
    chat_url: str | None = None
    auth_token: str | None = None
    dataset_id: str | None = None
    driver_type: str = "http"


class AgentOut(BaseModel):
    id: str
    name: str
    mcp_url: str
    chat_url: str | None = None
    dataset_id: str | None = None
    driver_type: str | None = None
    rate_limit_qps: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentRegisterOut(AgentOut):
    api_key: str


class ToolOut(BaseModel):
    id: str
    agent_id: str
    name: str
    description: str
    status: str

    model_config = {"from_attributes": True}


class ProxyCallIn(BaseModel):
    agent_id: str
    tool_name: str
    arguments: dict[str, Any] = {}
    session_id: str = ""


class ProxyCallOut(BaseModel):
    trace_id: str
    result: Any
    latency_ms: int
    status: str


class TraceOut(BaseModel):
    id: int
    trace_id: str
    session_id: str
    agent_id: str
    tool_name: str
    params_masked_json: str
    result_summary: str
    status: str
    latency_ms: int
    token_usage: int
    cost: float
    error_code: str | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TraceIngestIn(BaseModel):
    session_id: str = ""
    tool_name: str
    arguments: dict[str, Any] = {}
    result_summary: str = ""
    status: str = "success"
    latency_ms: int = 0
    token_usage: int = 0
    cost: float = 0.0
    error_code: str | None = None
    error_message: str | None = None


class DatasetIn(BaseModel):
    name: str
    description: str = ""


class DatasetOut(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseIn(BaseModel):
    input_prompt: str
    expected_behavior: str = ""
    checks: list[dict] = []
    source_trace_id: str | None = None


class CaseOut(CaseIn):
    id: str
    dataset_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RunIn(BaseModel):
    dataset_id: str
    agent_version: str
    agent_id: str | None = None


class RunOut(BaseModel):
    id: str
    dataset_id: str
    agent_version: str
    agent_id: str | None = None
    status: str
    started_at: datetime
    finished_at: datetime | None
    summary_json: str | None

    model_config = {"from_attributes": True}


class CaseResultOut(BaseModel):
    case_id: str
    input_prompt: str
    deterministic_pass: bool
    judge_score: int | None
    judge_reason: str | None
    judge_degraded: bool
    overall_pass: bool


class RunDetailOut(RunOut):
    results: list[CaseResultOut] = []


class RegressionRow(BaseModel):
    case_id: str
    input_prompt: str
    baseline_pass: bool | None
    current_pass: bool | None
    baseline_score: int | None
    current_score: int | None


class RegressionOut(BaseModel):
    baseline_run_id: str
    current_run_id: str
    pass_rate_baseline: float
    pass_rate_current: float
    avg_score_baseline: float | None
    avg_score_current: float | None
    new_failures: list[str]
    rows: list[RegressionRow]


class MetricsOverview(BaseModel):
    trace_total: int
    success_rate: float
    avg_latency_ms: float
    total_cost: float
    last_run_pass_rate: float | None


class TrendPoint(BaseModel):
    day: str
    pass_rate: float | None
    avg_score: float | None


class ReviewItemIn(BaseModel):
    trace_id: str


class ReviewItemOut(BaseModel):
    id: int
    trace_id: str
    status: str
    reviewer_note: str | None
    created_at: datetime
    decided_at: datetime | None

    model_config = {"from_attributes": True}


class ReviewDecideIn(BaseModel):
    status: str
    note: str = ""
    promote_to_dataset_id: str | None = None
    input_prompt: str | None = None