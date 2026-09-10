from datetime import UTC, datetime, time, timedelta
from typing import Any, Literal
import uuid
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.modules.connections.ingress import sync_connection
from app.modules.connections.models import Credential
from app.modules.connections.providers import ProviderFailure, telegram
from app.modules.connections.vault import get_secret, store_credential
from app.modules.executions.engine import finish_step
from app.modules.executions.models import Approval, Delivery, RunStep, WorkflowRun
from app.modules.identity.dependencies import AuthContext, require_auth, require_csrf
from app.modules.identity.models import Tenant
from app.modules.lite.models import (
    AgentProfile,
    Connection,
    InboundMessage,
    LiteWorkflow,
)
from app.modules.registry.graph import Graph, digest, manifests
from app.modules.workflows.models import WorkflowVersion
from app.modules.workflows.service import (
    compile_graph,
    enqueue,
    event,
    owned,
    publish,
    require_role,
)

router = APIRouter(tags=["workflow-platform"])


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorkflowCreate(Payload):
    name: str = Field(default="Untitled workflow", min_length=1, max_length=180)
    description: str = Field(default="", max_length=2000)
    graph_json: dict = Field(
        default_factory=lambda: {
            "schema_version": 1,
            "nodes": [
                {
                    "id": "trigger",
                    "type": "manual_trigger",
                    "label": "Manual trigger",
                    "x": 80,
                    "y": 160,
                    "config": {},
                }
            ],
            "edges": [],
        }
    )

    @field_validator("graph_json")
    @classmethod
    def validate_shape(cls, value):
        # Drafts may have incomplete connections/configuration, but must be renderable.
        return Graph.model_validate(value).model_dump()


class WorkflowEdit(WorkflowCreate):
    revision: int = Field(ge=1)


class Revision(Payload):
    revision: int


class RunInput(Payload):
    mode: Literal["dry_run", "live"] = "dry_run"
    payload: dict[str, Any] = Field(default_factory=dict)
    version_id: uuid.UUID | None = None


class Activation(Payload):
    enabled: bool
    mode: Literal["dry_run", "live"] = "dry_run"


class Decision(Payload):
    decision: Literal["approve", "reject"]
    snapshot_hash: str


class CredentialInput(Payload):
    name: str = Field(min_length=1, max_length=160)
    provider: Literal["telegram", "openrouter"]
    secret: SecretStr = Field(min_length=20, max_length=512)


class ConnectionInput(Payload):
    name: str = Field(min_length=1, max_length=160)
    credential_id: uuid.UUID | None = None
    polling: bool = False
    webhook_secret: SecretStr | None = Field(
        default=None, min_length=16, max_length=256
    )


class AgentInput(Payload):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    provider: Literal["openrouter"] = "openrouter"
    model: str = Field(default="", max_length=160)
    system_prompt: str = Field(
        default="Bạn là trợ lý hỗ trợ. Trả lời ngắn gọn, lịch sự bằng tiếng Việt.",
        max_length=12000,
    )
    credential_id: uuid.UUID | None = None


class MessageInput(Payload):
    body: str = Field(min_length=1, max_length=12000)
    sender_name: str = Field(default="Demo visitor", min_length=1, max_length=180)


def fields(item, names):
    return {name: getattr(item, name) for name in names.split()}


def workflow_view(w):
    return fields(
        w,
        "id name description slug status active_version revision enabled execution_mode graph_json updated_at",
    )


def run_view(r):
    result = fields(
        r,
        "id workflow_id version_id mode status trigger_channel input_preview error started_at completed_at next_node_id",
    )
    result["output_preview"] = r.context_json.get("data", {}).get(
        "reply"
    ) or r.context_json.get("data", {}).get("text")
    return result


@router.get("/modules")
def modules(context: AuthContext = Depends(require_auth)):
    return manifests()


@router.get("/workflows")
def workflows(
    context: AuthContext = Depends(require_auth), db: Session = Depends(get_db)
):
    return [
        workflow_view(w)
        for w in db.scalars(
            select(LiteWorkflow)
            .where(LiteWorkflow.tenant_id == context.membership.tenant_id)
            .order_by(LiteWorkflow.updated_at.desc())
            .limit(200)
        )
    ]


@router.post("/workflows", status_code=201)
def create_workflow(
    payload: WorkflowCreate,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner", "builder")
    w = LiteWorkflow(
        tenant_id=context.membership.tenant_id,
        slug=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
        graph_json=payload.graph_json,
        active_version=0,
    )
    db.add(w)
    db.flush()
    event(db, w.tenant_id, "workflow.created", w.id)
    db.commit()
    return workflow_view(w)


@router.get("/workflows/{ident}")
def get_workflow(
    ident: uuid.UUID,
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    return workflow_view(owned(db, LiteWorkflow, context.membership.tenant_id, ident))


@router.patch("/workflows/{ident}")
def save_workflow(
    ident: uuid.UUID,
    payload: WorkflowEdit,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner", "builder")
    w = owned(db, LiteWorkflow, context.membership.tenant_id, ident, lock=True)
    if w.revision != payload.revision:
        raise HTTPException(
            409, "This draft changed in another tab. Reload before saving."
        )
    # Drafts may be incomplete. Publish enforces the full graph contract.
    stmt = (
        update(LiteWorkflow)
        .where(LiteWorkflow.id == ident, LiteWorkflow.revision == payload.revision)
        .values(
            name=payload.name,
            description=payload.description,
            graph_json=payload.graph_json,
            status="draft",
            revision=payload.revision + 1,
        )
    )
    if db.execute(stmt).rowcount != 1:
        raise HTTPException(409, "Draft revision conflict")
    event(db, w.tenant_id, "workflow.saved", w.id)
    db.commit()
    db.refresh(w)
    return workflow_view(w)


@router.post("/workflows/{ident}/validate")
def validate_workflow(
    ident: uuid.UUID,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    w = owned(db, LiteWorkflow, context.membership.tenant_id, ident)
    _, errors = compile_graph(db, w.tenant_id, w.graph_json)
    return {"valid": not errors, "errors": errors}


@router.post("/workflows/{ident}/publish")
def publish_workflow(
    ident: uuid.UUID,
    payload: Revision,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner", "builder")
    w = owned(db, LiteWorkflow, context.membership.tenant_id, ident, lock=True)
    if w.revision != payload.revision:
        raise HTTPException(409, "Draft revision conflict; reload the workflow")
    if w.enabled and w.execution_mode == "live":
        require_role(context, "owner")
    version = publish(db, w, context.user.id)
    db.commit()
    return {"workflow": workflow_view(w), "version_id": version.id}


@router.get("/workflows/{ident}/versions")
def versions(
    ident: uuid.UUID,
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    w = owned(db, LiteWorkflow, context.membership.tenant_id, ident)
    return [
        fields(v, "id number graph_hash created_at")
        for v in db.scalars(
            select(WorkflowVersion)
            .where(WorkflowVersion.workflow_id == w.id)
            .order_by(WorkflowVersion.number.desc())
        )
    ]


@router.post("/workflows/{ident}/runs", status_code=201)
def start_run(
    ident: uuid.UUID,
    payload: RunInput,
    idempotency_key: str = Header(default=""),
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner", "builder")
    w = owned(db, LiteWorkflow, context.membership.tenant_id, ident)
    r = enqueue(
        db,
        w,
        context.user.id,
        payload.mode,
        payload.payload,
        idempotency_key,
        payload.version_id,
    )
    db.commit()
    return run_view(r)


@router.post("/workflows/{ident}/activation")
def activate(
    ident: uuid.UUID,
    payload: Activation,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner")
    w = owned(db, LiteWorkflow, context.membership.tenant_id, ident, lock=True)
    v = db.scalar(
        select(WorkflowVersion).where(
            WorkflowVersion.workflow_id == w.id,
            WorkflowVersion.number == w.active_version,
        )
    )
    if payload.enabled and not v:
        raise HTTPException(409, "Publish before activating")
    if payload.mode == "live" and get_settings().outbound_mode != "live":
        raise HTTPException(
            409, "Set OUTBOUND_MODE=live on the server before activating live execution"
        )
    w.enabled = payload.enabled
    w.execution_mode = payload.mode
    w.revision += 1
    event(
        db,
        w.tenant_id,
        "workflow.activation",
        w.id,
        enabled=w.enabled,
        mode=w.execution_mode,
    )
    db.commit()
    return workflow_view(w)


@router.get("/runs")
def runs(
    status: str | None = None,
    limit: int = Query(100, ge=1, le=200),
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    stmt = select(WorkflowRun).where(
        WorkflowRun.tenant_id == context.membership.tenant_id
    )
    if status:
        stmt = stmt.where(WorkflowRun.status == status)
    return [
        run_view(r)
        for r in db.scalars(stmt.order_by(WorkflowRun.started_at.desc()).limit(limit))
    ]


@router.get("/runs/{ident}")
def get_run(
    ident: uuid.UUID,
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    r = owned(db, WorkflowRun, context.membership.tenant_id, ident)
    v = owned(db, WorkflowVersion, r.tenant_id, r.version_id)
    approvals = [
        fields(a, "id node_id status snapshot snapshot_hash decided_at")
        for a in db.scalars(select(Approval).where(Approval.run_id == r.id))
    ]
    steps = [
        fields(
            s,
            "id node_id node_type status input_json output_json error started_at completed_at",
        )
        for s in db.scalars(select(RunStep).where(RunStep.run_id == r.id))
    ]
    return {
        **run_view(r),
        "version_number": v.number,
        "steps": steps,
        "approvals": approvals,
        "graph_json": v.graph_json,
        "input": r.context_json.get("input", {}),
    }


@router.post("/runs/{ident}/cancel")
def cancel_run(
    ident: uuid.UUID,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner", "builder")
    r = owned(db, WorkflowRun, context.membership.tenant_id, ident, lock=True)
    if r.mode == "live":
        require_role(context, "owner")
    if r.status in ("succeeded", "failed", "cancelled", "rejected", "delivery_unknown"):
        raise HTTPException(409, "This run is already terminal")
    deliveries = list(db.scalars(select(Delivery).where(Delivery.run_id == r.id)))
    if any(d.status == "dispatching" for d in deliveries):
        raise HTTPException(
            409, "Sending is in progress; wait for the provider receipt"
        )
    for d in deliveries:
        if d.status == "pending":
            d.status = "cancelled"
    for a in db.scalars(
        select(Approval).where(Approval.run_id == r.id, Approval.status == "pending")
    ):
        a.status = "cancelled"
    for s in db.scalars(select(RunStep).where(RunStep.run_id == r.id)):
        if s.status not in ("succeeded", "skipped"):
            s.status = "cancelled"
    r.status = "cancelled"
    r.completed_at = datetime.now(UTC)
    event(db, r.tenant_id, "run.updated", r.id, status=r.status)
    db.commit()
    return run_view(r)


@router.post("/approvals/{ident}/decide")
def decide(
    ident: uuid.UUID,
    payload: Decision,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner", "reviewer")
    a = owned(db, Approval, context.membership.tenant_id, ident)
    r = owned(db, WorkflowRun, a.tenant_id, a.run_id, lock=True)
    db.refresh(a)
    if payload.snapshot_hash != a.snapshot_hash:
        raise HTTPException(409, "The action snapshot does not match")
    wanted = "approved" if payload.decision == "approve" else "rejected"
    if a.status != "pending":
        if a.status == wanted:
            return {"status": a.status, "run_id": a.run_id}
        raise HTTPException(409, "This approval has already been decided")
    if r.status != "waiting_human":
        raise HTTPException(409, "Run is no longer waiting for approval")
    result = db.execute(
        update(Approval)
        .where(Approval.id == a.id, Approval.status == "pending")
        .values(status=wanted, decided_by=context.user.id, decided_at=datetime.now(UTC))
    )
    if result.rowcount != 1:
        raise HTTPException(409, "Another reviewer already decided")
    step = db.scalar(
        select(RunStep).where(RunStep.run_id == r.id, RunStep.node_id == a.node_id)
    )
    if wanted == "approved":
        v = owned(db, WorkflowVersion, r.tenant_id, r.version_id)
        finish_step(db, r, step, {"approved": True}, v.graph_json)
    else:
        r.status = "rejected"
        r.completed_at = datetime.now(UTC)
        step.status = "rejected"
        for s in db.scalars(
            select(RunStep).where(RunStep.run_id == r.id, RunStep.status == "pending")
        ):
            s.status = "skipped"
    event(
        db,
        r.tenant_id,
        "approval.decided",
        r.id,
        decision=wanted,
        actor_id=str(context.user.id),
    )
    db.commit()
    return {"status": wanted, "run_id": r.id}


@router.get("/credentials")
def credentials(
    context: AuthContext = Depends(require_auth), db: Session = Depends(get_db)
):
    require_role(context, "owner", "builder")
    return [
        fields(c, "id name provider status")
        for c in db.scalars(
            select(Credential)
            .where(Credential.tenant_id == context.membership.tenant_id)
            .order_by(Credential.created_at.desc())
        )
    ]


@router.post("/credentials", status_code=201)
def create_credential(
    payload: CredentialInput,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner")
    c = store_credential(
        db,
        context.membership.tenant_id,
        payload.provider,
        payload.name,
        payload.secret.get_secret_value().strip(),
    )
    event(db, c.tenant_id, "credential.created", c.id, provider=c.provider)
    db.commit()
    return fields(c, "id name provider status")


@router.delete("/credentials/{ident}")
def revoke_credential(
    ident: uuid.UUID,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner")
    c = owned(db, Credential, context.membership.tenant_id, ident)
    c.status = "revoked"
    c.ciphertext = ""
    event(db, c.tenant_id, "credential.revoked", c.id)
    db.commit()
    return {"status": "revoked"}


@router.get("/connections")
def connections(
    context: AuthContext = Depends(require_auth), db: Session = Depends(get_db)
):
    return [
        connection_view(c)
        for c in db.scalars(
            select(Connection)
            .where(Connection.tenant_id == context.membership.tenant_id)
            .order_by(Connection.created_at)
        )
    ]


def connection_view(c):
    return {
        **fields(c, "id name slug provider status last_checked_at"),
        "configured": bool(c.credential_ref and c.credential_ref.startswith("vault:")),
        "polling": bool(c.config.get("polling")),
        "bot_username": c.config.get("bot_username"),
        "webhook_configured": bool(c.config.get("webhook_hash")),
    }


@router.post("/connections", status_code=201)
def new_connection(
    payload: ConnectionInput,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner")
    c = Connection(
        tenant_id=context.membership.tenant_id,
        slug=str(uuid.uuid4()),
        name=payload.name,
        provider="telegram",
        status="needs_setup",
        config={},
    )
    db.add(c)
    db.flush()
    return configure_connection(c.id, payload, context, db)


@router.patch("/connections/{ident}")
def configure_connection(
    ident: uuid.UUID,
    payload: ConnectionInput,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner")
    c = owned(db, Connection, context.membership.tenant_id, ident, lock=True)
    if c.provider != "telegram":
        raise HTTPException(
            409, "This connector is not implemented in the Lite release"
        )
    if payload.credential_id:
        cred = owned(db, Credential, c.tenant_id, payload.credential_id)
        if cred.provider != "telegram" or cred.status != "active":
            raise HTTPException(422, "Choose an active Telegram credential")
        if c.credential_ref != f"vault:{cred.id}":
            c.credential_ref = f"vault:{cred.id}"
            c.status = "needs_test"
            c.config = {}
    c.name = payload.name
    c.config = {**c.config, "polling": payload.polling}
    if payload.webhook_secret:
        c.config = {
            **c.config,
            "webhook_hash": digest(payload.webhook_secret.get_secret_value()),
        }
    if payload.polling and c.config.get("webhook_hash"):
        raise HTTPException(422, "Use polling or webhook delivery, not both")
    event(db, c.tenant_id, "connection.updated", c.id)
    db.commit()
    return connection_view(c)


@router.post("/connections/{ident}/test")
def test_connection(
    ident: uuid.UUID,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner")
    c = owned(db, Connection, context.membership.tenant_id, ident, lock=True)
    if c.provider != "telegram":
        raise HTTPException(409, "Connector is not available yet")
    try:
        token = get_secret(
            db, c.tenant_id, (c.credential_ref or "").removeprefix("vault:"), "telegram"
        )
        bot = telegram(token, "getMe")
        c.status = "active"
        c.config = {**c.config, "bot_username": bot.get("username")}
    except (ValueError, ProviderFailure) as exc:
        c.status = "needs_setup"
        db.commit()
        raise HTTPException(422, str(exc)) from None
    c.last_checked_at = datetime.now(UTC)
    event(db, c.tenant_id, "connection.updated", c.id)
    db.commit()
    return connection_view(c)


@router.post("/connections/{ident}/sync")
def sync(
    ident: uuid.UUID,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner")
    c = owned(db, Connection, context.membership.tenant_id, ident, lock=True)
    if c.provider != "telegram" or c.status != "active":
        raise HTTPException(409, "Test the Telegram connection first")
    if c.config.get("webhook_hash"):
        raise HTTPException(409, "This connection uses webhooks")
    try:
        count = sync_connection(db, c)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    return {"received": count}


def agent_view(a):
    return fields(
        a, "id name slug description provider model system_prompt credential_id status"
    )


@router.get("/agents")
def agents(context: AuthContext = Depends(require_auth), db: Session = Depends(get_db)):
    return [
        agent_view(a)
        for a in db.scalars(
            select(AgentProfile).where(
                AgentProfile.tenant_id == context.membership.tenant_id
            )
        )
    ]


@router.post("/agents", status_code=201)
def create_agent(
    payload: AgentInput,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner", "builder")
    a = AgentProfile(
        tenant_id=context.membership.tenant_id,
        slug=str(uuid.uuid4()),
        name=payload.name,
    )
    db.add(a)
    db.flush()
    return edit_agent(a.id, payload, context, db)


@router.patch("/agents/{ident}")
def edit_agent(
    ident: uuid.UUID,
    payload: AgentInput,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner", "builder")
    a = owned(db, AgentProfile, context.membership.tenant_id, ident)
    if payload.credential_id:
        c = owned(db, Credential, a.tenant_id, payload.credential_id)
        if c.provider != "openrouter" or c.status != "active":
            raise HTTPException(422, "Choose an active OpenRouter credential")
    for k, v in payload.model_dump().items():
        setattr(a, k, v)
    a.status = "configured" if a.credential_id and a.model else "demo"
    event(db, a.tenant_id, "agent.updated", a.id)
    db.commit()
    return agent_view(a)


@router.get("/inbox")
def inbox(
    channel: str | None = None,
    q: str = Query("", max_length=200),
    limit: int = Query(100, ge=1, le=200),
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    stmt = select(InboundMessage).where(
        InboundMessage.tenant_id == context.membership.tenant_id
    )
    if channel:
        stmt = stmt.where(InboundMessage.channel == channel)
    if q:
        stmt = stmt.where(
            InboundMessage.body.icontains(q, autoescape=True)
            | InboundMessage.sender_name.icontains(q, autoescape=True)
        )
    return [
        {
            **fields(
                m,
                "id connection_id channel sender_name sender_handle body ai_summary status received_at external_thread_id",
            ),
            "demo": bool(m.metadata_json.get("demo")),
        }
        for m in db.scalars(
            stmt.order_by(InboundMessage.received_at.desc()).limit(limit)
        )
    ]


@router.post("/inbox/demo", status_code=201)
def demo_message(
    payload: MessageInput,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner", "builder")
    m = InboundMessage(
        tenant_id=context.membership.tenant_id,
        channel="manual",
        sender_name=payload.sender_name,
        body=payload.body,
        status="new",
        received_at=datetime.now(UTC),
        metadata_json={"demo": True},
        external_thread_id="demo-chat",
    )
    db.add(m)
    db.flush()
    event(db, m.tenant_id, "message.received", m.id)
    db.commit()
    return {"id": m.id}


@router.patch("/inbox/{ident}/read")
def read_message(
    ident: uuid.UUID,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    require_role(context, "owner", "builder", "reviewer")
    m = owned(db, InboundMessage, context.membership.tenant_id, ident)
    m.status = "read"
    db.commit()
    return {"status": m.status}


@router.get("/overview")
def overview(
    context: AuthContext = Depends(require_auth), db: Session = Depends(get_db)
):
    tenant_id = context.membership.tenant_id
    tenant = db.get(Tenant, tenant_id)
    zone = ZoneInfo(tenant.timezone)
    today = datetime.now(zone).date()
    start = datetime.combine(today, time.min, zone).astimezone(UTC)
    end = datetime.combine(today + timedelta(days=1), time.min, zone).astimezone(UTC)

    def count(cls, *extra):
        return (
            db.scalar(
                select(func.count())
                .select_from(cls)
                .where(cls.tenant_id == tenant_id, *extra)
            )
            or 0
        )

    by_channel = dict(
        db.execute(
            select(InboundMessage.channel, func.count())
            .where(
                InboundMessage.tenant_id == tenant_id,
                InboundMessage.received_at >= start,
                InboundMessage.received_at < end,
            )
            .group_by(InboundMessage.channel)
        ).all()
    )
    statuses = dict(
        db.execute(
            select(WorkflowRun.status, func.count())
            .where(WorkflowRun.tenant_id == tenant_id)
            .group_by(WorkflowRun.status)
        ).all()
    )
    return {
        "connections_total": count(Connection),
        "connections_active": count(Connection, Connection.status == "active"),
        "messages_today": count(
            InboundMessage,
            InboundMessage.received_at >= start,
            InboundMessage.received_at < end,
        ),
        "unread": count(InboundMessage, InboundMessage.status == "new"),
        "agents_total": count(AgentProfile),
        "workflows_total": count(LiteWorkflow),
        "workflows_active": count(LiteWorkflow, LiteWorkflow.enabled.is_(True)),
        "runs_total": sum(statuses.values()),
        "runs_success": statuses.get("succeeded", 0),
        "pending_approvals": count(Approval, Approval.status == "pending"),
        "channel_counts": by_channel,
        "run_statuses": statuses,
        "timezone": tenant.timezone,
        "outbound_mode": get_settings().outbound_mode,
    }
