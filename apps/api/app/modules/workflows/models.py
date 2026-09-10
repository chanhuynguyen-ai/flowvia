"""Published graphs are immutable; preview drafts remain upgrade compatible."""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkflowVersion(Base):
    __tablename__ = "workflow_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_versions_tenant_id"),
        UniqueConstraint("workflow_id", "number", name="uq_versions_number"),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_id"],
            ["lite_workflows.tenant_id", "lite_workflows.id"],
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(index=True)
    number: Mapped[int] = mapped_column()
    graph_json: Mapped[dict] = mapped_column(JSON)
    graph_hash: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
