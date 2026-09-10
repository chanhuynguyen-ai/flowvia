"""M2 Lite product preview: omni-channel entities and workflow demo.

Revision ID: 20260908_0002
Revises: 20260908_0001
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260908_0002"
down_revision: str | Sequence[str] | None = "20260908_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=48), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("credential_ref", sa.String(length=255), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_connections_tenant_slug"),
    )
    op.create_index(
        "ix_connections_tenant_id", "connections", ["tenant_id"], unique=False
    )
    op.create_index(
        "ix_connections_provider", "connections", ["provider"], unique=False
    )
    op.create_index("ix_connections_status", "connections", ["status"], unique=False)
    op.create_index(
        "ix_connections_tenant_status",
        "connections",
        ["tenant_id", "status"],
        unique=False,
    )

    op.create_table(
        "agent_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=48), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_agents_tenant_slug"),
    )
    op.create_index(
        "ix_agent_profiles_tenant_id", "agent_profiles", ["tenant_id"], unique=False
    )
    op.create_index(
        "ix_agent_profiles_status", "agent_profiles", ["status"], unique=False
    )
    op.create_index(
        "ix_agents_tenant_status",
        "agent_profiles",
        ["tenant_id", "status"],
        unique=False,
    )

    op.create_table(
        "lite_workflows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("active_version", sa.Integer(), nullable=False),
        sa.Column("graph_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_lite_workflows_tenant_slug"),
    )
    op.create_index(
        "ix_lite_workflows_tenant_id", "lite_workflows", ["tenant_id"], unique=False
    )
    op.create_index(
        "ix_lite_workflows_status", "lite_workflows", ["status"], unique=False
    )
    op.create_index(
        "ix_lite_workflows_tenant_status",
        "lite_workflows",
        ["tenant_id", "status"],
        unique=False,
    )

    op.create_table(
        "inbound_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=True),
        sa.Column("channel", sa.String(length=48), nullable=False),
        sa.Column("external_thread_id", sa.String(length=255), nullable=True),
        sa.Column("external_message_id", sa.String(length=255), nullable=True),
        sa.Column("sender_name", sa.String(length=180), nullable=False),
        sa.Column("sender_handle", sa.String(length=180), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_inbound_messages_tenant_id", "inbound_messages", ["tenant_id"], unique=False
    )
    op.create_index(
        "ix_inbound_messages_connection_id",
        "inbound_messages",
        ["connection_id"],
        unique=False,
    )
    op.create_index(
        "ix_inbound_messages_channel", "inbound_messages", ["channel"], unique=False
    )
    op.create_index(
        "ix_inbound_messages_status", "inbound_messages", ["status"], unique=False
    )
    op.create_index(
        "ix_messages_tenant_received",
        "inbound_messages",
        ["tenant_id", "received_at"],
        unique=False,
    )
    op.create_index(
        "ix_messages_tenant_channel",
        "inbound_messages",
        ["tenant_id", "channel"],
        unique=False,
    )

    op.create_table(
        "lite_workflow_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("trigger_channel", sa.String(length=48), nullable=False),
        sa.Column("input_preview", sa.Text(), nullable=False),
        sa.Column("output_preview", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["workflow_id"], ["lite_workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_lite_workflow_runs_tenant_id",
        "lite_workflow_runs",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_lite_workflow_runs_workflow_id",
        "lite_workflow_runs",
        ["workflow_id"],
        unique=False,
    )
    op.create_index(
        "ix_lite_workflow_runs_status", "lite_workflow_runs", ["status"], unique=False
    )
    op.create_index(
        "ix_lite_runs_tenant_started",
        "lite_workflow_runs",
        ["tenant_id", "started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("lite_workflow_runs")
    op.drop_table("inbound_messages")
    op.drop_table("lite_workflows")
    op.drop_table("agent_profiles")
    op.drop_table("connections")
