"""durable_workflow_runtime

Revision ID: 20260910_0003
Revises: 20260908_0002
Create Date: 2026-09-10 16:33:33.996378
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260910_0003"
down_revision: Union[str, Sequence[str], None] = "20260908_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "credentials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=48), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_credentials_tenant_id"),
    )
    with op.batch_alter_table("credentials", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_credentials_tenant_id"), ["tenant_id"], unique=False
        )

    op.create_table(
        "runtime_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("topic", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("runtime_events", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_runtime_events_tenant_id"), ["tenant_id"], unique=False
        )

    with op.batch_alter_table("lite_workflows", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("revision", sa.Integer(), server_default="1", nullable=False)
        )
        batch_op.add_column(
            sa.Column("enabled", sa.Boolean(), server_default="false", nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "execution_mode",
                sa.String(length=24),
                server_default="dry_run",
                nullable=False,
            )
        )
        batch_op.create_unique_constraint("uq_workflows_tenant_id", ["tenant_id", "id"])

    op.create_table(
        "workflow_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("graph_json", sa.JSON(), nullable=False),
        sa.Column("graph_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_id"],
            ["lite_workflows.tenant_id", "lite_workflows.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_versions_tenant_id"),
        sa.UniqueConstraint("workflow_id", "number", name="uq_versions_number"),
    )
    with op.batch_alter_table("workflow_versions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_workflow_versions_tenant_id"), ["tenant_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_workflow_versions_workflow_id"),
            ["workflow_id"],
            unique=False,
        )

    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("mode", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("trigger_channel", sa.String(length=48), nullable=False),
        sa.Column("input_preview", sa.Text(), nullable=False),
        sa.Column("context_json", sa.JSON(), nullable=False),
        sa.Column("next_node_id", sa.String(length=100), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "version_id"],
            ["workflow_versions.tenant_id", "workflow_versions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_id"],
            ["lite_workflows.tenant_id", "lite_workflows.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_runs_tenant_id"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_runs_idempotency"),
    )
    with op.batch_alter_table("workflow_runs", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_workflow_runs_status"), ["status"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_workflow_runs_tenant_id"), ["tenant_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_workflow_runs_version_id"), ["version_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_workflow_runs_workflow_id"), ["workflow_id"], unique=False
        )

    op.create_table(
        "approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("node_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("decided_by", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["decided_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "run_id"],
            ["workflow_runs.tenant_id", "workflow_runs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "node_id", name="uq_approval_node"),
    )
    with op.batch_alter_table("approvals", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_approvals_run_id"), ["run_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_approvals_tenant_id"), ["tenant_id"], unique=False
        )

    op.create_table(
        "deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("node_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("provider_message_id", sa.String(length=100), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "run_id"],
            ["workflow_runs.tenant_id", "workflow_runs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "node_id", name="uq_delivery_node"),
    )
    with op.batch_alter_table("deliveries", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_deliveries_run_id"), ["run_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_deliveries_status"), ["status"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_deliveries_tenant_id"), ["tenant_id"], unique=False
        )

    op.create_table(
        "run_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("node_id", sa.String(length=100), nullable=False),
        sa.Column("node_type", sa.String(length=48), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("input_json", sa.JSON(), nullable=False),
        sa.Column("output_json", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id", "run_id"],
            ["workflow_runs.tenant_id", "workflow_runs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "node_id", name="uq_steps_node"),
    )
    with op.batch_alter_table("run_steps", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_run_steps_run_id"), ["run_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_run_steps_tenant_id"), ["tenant_id"], unique=False
        )

    with op.batch_alter_table("agent_profiles", schema=None) as batch_op:
        batch_op.add_column(sa.Column("credential_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_agent_credential_tenant",
            "credentials",
            ["tenant_id", "credential_id"],
            ["tenant_id", "id"],
        )

    with op.batch_alter_table("connections", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_connections_tenant_id", ["tenant_id", "id"]
        )

    with op.batch_alter_table("inbound_messages", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_inbound_external", ["connection_id", "external_message_id"]
        )
        batch_op.create_foreign_key(
            "fk_message_connection_tenant",
            "connections",
            ["tenant_id", "connection_id"],
            ["tenant_id", "id"],
        )


def downgrade() -> None:
    for table in (
        "run_steps",
        "deliveries",
        "approvals",
        "workflow_runs",
        "workflow_versions",
        "runtime_events",
    ):
        op.drop_table(table)
    with op.batch_alter_table("inbound_messages") as batch_op:
        batch_op.drop_constraint("fk_message_connection_tenant", type_="foreignkey")
        batch_op.drop_constraint("uq_inbound_external", type_="unique")
    with op.batch_alter_table("agent_profiles") as batch_op:
        batch_op.drop_constraint("fk_agent_credential_tenant", type_="foreignkey")
        batch_op.drop_column("credential_id")
    op.drop_table("credentials")
    with op.batch_alter_table("connections") as batch_op:
        batch_op.drop_constraint("uq_connections_tenant_id", type_="unique")
    with op.batch_alter_table("lite_workflows") as batch_op:
        batch_op.drop_constraint("uq_workflows_tenant_id", type_="unique")
        batch_op.drop_column("execution_mode")
        batch_op.drop_column("enabled")
        batch_op.drop_column("revision")
