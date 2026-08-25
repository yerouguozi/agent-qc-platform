import json
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.core.db import Base


def new_id() -> str:
    return uuid.uuid4().hex


class Agent(Base):
    __tablename__ = "agents"
    id = Column(String(32), primary_key=True, default=new_id)
    name = Column(String(100), nullable=False)
    mcp_url = Column(String(500), nullable=False)
    chat_url = Column(String(500), nullable=True)
    auth_token = Column(Text, nullable=True)
    dataset_id = Column(String(100), nullable=True)
    driver_type = Column(String(20), default="http", nullable=False)
    api_key_hash = Column(String(128), nullable=False)
    rate_limit_qps = Column(Integer, default=5, nullable=False)
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Tool(Base):
    __tablename__ = "tools"
    id = Column(String(32), primary_key=True, default=new_id)
    agent_id = Column(String(32), ForeignKey("agents.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    input_schema_json = Column(Text, default="{}")
    status = Column(String(20), default="active")
    synced_at = Column(DateTime, default=datetime.utcnow)


class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(String(32), primary_key=True, default=new_id)
    agent_id = Column(String(32), ForeignKey("agents.id"), nullable=False, index=True)
    key_hash = Column(String(128), nullable=False)
    scopes = Column(String(100), default="all")
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)


class Trace(Base):
    __tablename__ = "traces"
    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(32), unique=True, nullable=False, default=new_id)
    session_id = Column(String(100), default="", index=True)
    agent_id = Column(String(32), ForeignKey("agents.id"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    params_masked_json = Column(Text, default="{}")
    result_summary = Column(Text, default="")
    status = Column(String(20), nullable=False)
    latency_ms = Column(Integer, default=0)
    token_usage = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ChatSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    external_session_id = Column(String(100), unique=True, nullable=False)
    agent_id = Column(String(32), ForeignKey("agents.id"), nullable=False)
    user_ref = Column(String(100), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)


class EvalDataset(Base):
    __tablename__ = "eval_datasets"
    id = Column(String(32), primary_key=True, default=new_id)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class EvalCase(Base):
    __tablename__ = "eval_cases"
    id = Column(String(32), primary_key=True, default=new_id)
    dataset_id = Column(String(32), ForeignKey("eval_datasets.id"), nullable=False, index=True)
    input_prompt = Column(Text, nullable=False)
    expected_behavior = Column(Text, default="")
    checks_json = Column(Text, default="[]")
    source_trace_id = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def checks(self) -> list:
        return json.loads(self.checks_json or "[]")


class EvalRun(Base):
    __tablename__ = "eval_runs"
    id = Column(String(32), primary_key=True, default=new_id)
    dataset_id = Column(String(32), ForeignKey("eval_datasets.id"), nullable=False, index=True)
    agent_version = Column(String(100), nullable=False)
    agent_id = Column(String(32), nullable=True, index=True)
    status = Column(String(20), default="running")
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    summary_json = Column(Text, nullable=True)


class EvalResult(Base):
    __tablename__ = "eval_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(32), ForeignKey("eval_runs.id"), nullable=False, index=True)
    case_id = Column(String(32), ForeignKey("eval_cases.id"), nullable=False)
    trace_id = Column(String(32), nullable=True)
    deterministic_pass = Column(Boolean, nullable=False)
    judge_score = Column(Integer, nullable=True)
    judge_reason = Column(Text, nullable=True)
    judge_degraded = Column(Boolean, default=False)
    overall_pass = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(32), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    request_id = Column(String(64), default="", index=True)
    source = Column(String(100), default="")
    result = Column(String(20), default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ReviewItem(Base):
    __tablename__ = "review_queue"
    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(32), ForeignKey("traces.trace_id"), nullable=False, unique=True)
    status = Column(String(20), default="pending")
    reviewer_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)