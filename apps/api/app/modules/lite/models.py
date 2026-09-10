import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Connection(Base):
    __tablename__ = "connections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_connections_tenant_id"),
        UniqueConstraint("tenant_id", "slug", name="uq_connections_tenant_slug"),
        Index("ix_connections_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    slug: Mapped[str] = mapped_column(String(120))
    provider: Mapped[str] = mapped_column(String(48), index=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(32), default="planned", index=True)
    credential_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InboundMessage(Base):
    __tablename__ = "inbound_messages"
    __table_args__ = (
        UniqueConstraint(
            "connection_id", "external_message_id", name="uq_inbound_external"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "connection_id"], ["connections.tenant_id", "connections.id"]
        ),
        Index("ix_messages_tenant_received", "tenant_id", "received_at"),
        Index("ix_messages_tenant_channel", "tenant_id", "channel"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    connection_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("connections.id"), nullable=True, index=True
    )
    channel: Mapped[str] = mapped_column(String(48), index=True)
    external_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_name: Mapped[str] = mapped_column(String(180))
    sender_handle: Mapped[str | None] = mapped_column(String(180), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AgentProfile(Base):
    __tablename__ = "agent_profiles"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "credential_id"], ["credentials.tenant_id", "credentials.id"]
        ),
        UniqueConstraint("tenant_id", "slug", name="uq_agents_tenant_slug"),
        Index("ix_agents_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    slug: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    provider: Mapped[str] = mapped_column(String(48), default="openrouter")
    model: Mapped[str] = mapped_column(String(160), default="")
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    credential_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LiteWorkflow(Base):
    __tablename__ = "lite_workflows"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_workflows_tenant_id"),
        UniqueConstraint("tenant_id", "slug", name="uq_lite_workflows_tenant_slug"),
        Index("ix_lite_workflows_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    slug: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    active_version: Mapped[int] = mapped_column(default=1)
    revision: Mapped[int] = mapped_column(default=1, server_default="1")
    enabled: Mapped[bool] = mapped_column(default=False, server_default="false")
    execution_mode: Mapped[str] = mapped_column(
        String(24), default="dry_run", server_default="dry_run"
    )
    graph_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LiteWorkflowRun(Base):
    __tablename__ = "lite_workflow_runs"
    __table_args__ = (Index("ix_lite_runs_tenant_started", "tenant_id", "started_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lite_workflows.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(32), index=True)
    trigger_channel: Mapped[str] = mapped_column(String(48))
    input_preview: Mapped[str] = mapped_column(Text, default="")
    output_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
