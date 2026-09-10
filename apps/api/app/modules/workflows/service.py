from copy import deepcopy
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.modules.connections.models import Credential
from app.modules.executions.models import RuntimeEvent, RunStep, WorkflowRun
from app.modules.identity.models import User
from app.modules.identity.service import get_membership
from app.modules.lite.models import AgentProfile, Connection, LiteWorkflow
from app.modules.registry.graph import digest, validate_graph
from app.modules.workflows.models import WorkflowVersion


def event(db, tenant_id, topic, resource_id, **data):
    db.add(
        RuntimeEvent(
            tenant_id=tenant_id, topic=topic, resource_id=str(resource_id), data=data
        )
    )


def owned(db, cls, tenant_id, ident, lock=False):
    try:
        ident = uuid.UUID(str(ident))
    except (ValueError, TypeError):
        raise HTTPException(404, "Resource not found") from None
    stmt = select(cls).where(cls.id == ident, cls.tenant_id == tenant_id)
    if lock:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    item = db.scalar(stmt)
    if item is None:
        raise HTTPException(404, "Resource not found")
    return item


def require_role(context, *roles):
    if context.membership.role not in roles:
        raise HTTPException(403, "Your workspace role cannot perform this action")


def can_execute(db, run):
    member = get_membership(db, run.created_by, run.tenant_id)
    user = db.get(User, run.created_by)
    if (
        member is None
        or user is None
        or user.status != "active"
        or member.role not in ("owner", "builder")
    ):
        raise ValueError("Workflow creator no longer has execution permission")
    if run.mode == "live" and (
        member.role != "owner" or get_settings().outbound_mode != "live"
    ):
        raise ValueError(
            "Live execution is disabled or the owner's permission was revoked"
        )


def compile_graph(db, tenant_id, raw):
    graph, errors = validate_graph(raw)
    if errors:
        return graph, errors
    for node in graph["nodes"]:
        config = node["config"]
        try:
            if node["type"] in ("telegram_trigger", "telegram_send"):
                if not config["connection_id"]:
                    errors.append(f"{node['label']}: choose a Telegram connection.")
                else:
                    connection = owned(
                        db, Connection, tenant_id, config["connection_id"]
                    )
                    if connection.provider != "telegram":
                        errors.append("This node requires a Telegram connection.")
            if node["type"] == "ai_agent":
                agent = owned(db, AgentProfile, tenant_id, config["agent_id"])
                if agent.status == "disabled":
                    errors.append("The selected agent is disabled.")
                node["agent_snapshot"] = {
                    "id": str(agent.id),
                    "name": agent.name,
                    "provider": agent.provider,
                    "model": agent.model,
                    "system_prompt": agent.system_prompt,
                    "credential_id": (
                        str(agent.credential_id) if agent.credential_id else None
                    ),
                }
        except HTTPException:
            errors.append(
                f"{node['label']}: selected resource is not available in this workspace."
            )
    return graph, errors


def publish(db, workflow, user_id):
    graph, errors = compile_graph(db, workflow.tenant_id, workflow.graph_json)
    if errors:
        raise HTTPException(422, {"errors": errors})
    number = (
        db.scalar(
            select(func.max(WorkflowVersion.number)).where(
                WorkflowVersion.workflow_id == workflow.id
            )
        )
        or 0
    ) + 1
    version = WorkflowVersion(
        tenant_id=workflow.tenant_id,
        workflow_id=workflow.id,
        number=number,
        graph_json=deepcopy(graph),
        graph_hash=digest(graph),
        created_by=user_id,
    )
    db.add(version)
    db.flush()
    workflow.active_version = number
    workflow.status = "published"
    workflow.revision += 1
    event(db, workflow.tenant_id, "workflow.published", workflow.id, version=number)
    return version


def enqueue(db, workflow, user_id, mode, payload, key, version_id=None):
    if not key or len(key) > 200:
        raise HTTPException(422, "An Idempotency-Key up to 200 characters is required")
    request_hash = digest(
        {
            "workflow": str(workflow.id),
            "version": str(version_id) if version_id else None,
            "mode": mode,
            "payload": payload,
        }
    )
    existing = db.scalar(
        select(WorkflowRun).where(
            WorkflowRun.tenant_id == workflow.tenant_id,
            WorkflowRun.idempotency_key == key,
        )
    )
    if existing:
        if existing.request_hash != request_hash:
            raise HTTPException(
                409, "Idempotency-Key was already used with different input"
            )
        return existing
    version = (
        owned(db, WorkflowVersion, workflow.tenant_id, version_id)
        if version_id
        else db.scalar(
            select(WorkflowVersion).where(
                WorkflowVersion.workflow_id == workflow.id,
                WorkflowVersion.number == workflow.active_version,
            )
        )
    )
    if version is None or version.workflow_id != workflow.id:
        raise HTTPException(409, "Publish the workflow before running it")
    graph = version.graph_json
    trigger = next(n for n in graph["nodes"] if n["type"].endswith("_trigger"))
    run = WorkflowRun(
        tenant_id=workflow.tenant_id,
        workflow_id=workflow.id,
        version_id=version.id,
        created_by=user_id,
        mode=mode,
        status="queued",
        idempotency_key=key,
        request_hash=request_hash,
        trigger_channel=(
            "telegram" if trigger["type"] == "telegram_trigger" else "manual"
        ),
        input_preview=str(payload.get("body", ""))[:1000],
        context_json={
            "input": deepcopy(payload),
            "data": deepcopy(payload),
            "steps": {},
        },
        next_node_id=trigger["id"],
    )
    try:
        can_execute(db, run)
    except ValueError as exc:
        raise HTTPException(403, str(exc)) from None
    # The savepoint handles simultaneous requests without rolling back an ingress message.
    try:
        with db.begin_nested():
            db.add(run)
            db.flush()
            for node in graph["nodes"]:
                db.add(
                    RunStep(
                        tenant_id=run.tenant_id,
                        run_id=run.id,
                        node_id=node["id"],
                        node_type=node["type"],
                        status="pending",
                    )
                )
            event(db, workflow.tenant_id, "run.queued", run.id, status="queued")
    except IntegrityError:
        existing = db.scalar(
            select(WorkflowRun).where(
                WorkflowRun.tenant_id == workflow.tenant_id,
                WorkflowRun.idempotency_key == key,
            )
        )
        if not existing or existing.request_hash != request_hash:
            raise HTTPException(409, "Conflicting run request") from None
        return existing
    return run
