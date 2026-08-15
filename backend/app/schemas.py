from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str


class AgentRegisterIn(BaseModel):
    name: str
    mcp_url: str
    rate_limit_qps: int = 5


class AgentOut(BaseModel):
    id: str
    name: str
    mcp_url: str
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