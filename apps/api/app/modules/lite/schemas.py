import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    provider: str
    name: str
    status: str
    credential_ref: str | None
    config: dict[str, Any]
    last_checked_at: datetime | None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel: str
    sender_name: str
    sender_handle: str | None
    body: str
    ai_summary: str | None
    status: str
    received_at: datetime


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str
    provider: str
    model: str
    status: str


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str
    status: str
    active_version: int
    graph_json: dict[str, Any]
    updated_at: datetime


class WorkflowRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    trigger_channel: str
    input_preview: str
    output_preview: str | None
    started_at: datetime
    completed_at: datetime | None


class OverviewResponse(BaseModel):
    connections_total: int
    connections_active: int
    messages_today: int
    agents_total: int
    workflows_total: int
    runs_total: int
    runs_success: int
    channel_counts: dict[str, int]


class TelegramTestResponse(BaseModel):
    configured: bool
    connected: bool
    bot_username: str | None = None
    bot_name: str | None = None
    message: str
