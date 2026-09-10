"""One durable step per transaction. Waiting for approval never holds a worker."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.modules.connections.providers import (
    agent_reply,
    telegram,
    DeliveryUnknown,
    ProviderFailure,
)
from app.modules.connections.vault import get_secret
from app.modules.executions.models import Approval, Delivery, RunStep, WorkflowRun
from app.modules.lite.models import Connection
from app.modules.registry.graph import digest, lookup, next_node, render
from app.modules.workflows.models import WorkflowVersion
from app.modules.workflows.service import can_execute, event, owned


def now():
    return datetime.now(UTC)


def action_snapshot(db, run, node):
    cfg = node["config"]
    if node["type"] == "record_action":
        return {
            "node_id": node["id"],
            "type": "record_action",
            "text": str(render(cfg["text"], run.context_json))[:4000],
            "mode": run.mode,
        }
    conn = owned(db, Connection, run.tenant_id, cfg["connection_id"])
    chat_id = str(render(cfg["chat_id"], run.context_json))
    text = str(render(cfg["text"], run.context_json))
    if not chat_id or not text or len(text) > 4096:
        raise ValueError("Telegram needs a chat ID and 1–4096 characters")
    if run.mode == "live" and conn.status != "active":
        raise ValueError("Telegram connection is not active")
    return {
        "node_id": node["id"],
        "type": "telegram_send",
        "connection_id": str(conn.id),
        "connection_name": conn.name,
        "credential_id": (conn.credential_ref or "").removeprefix("vault:"),
        "chat_id": chat_id,
        "text": text,
        "mode": run.mode,
    }


def finish_step(db, run, step, output, graph, port="out"):
    step.output_json = output
    step.status = "succeeded"
    step.completed_at = now()
    context = deepcopy(run.context_json)
    context["steps"][step.node_id] = output
    context["data"].update(output)
    run.context_json = context
    run.next_node_id = next_node(graph, step.node_id, port)
    run.status = "queued" if run.next_node_id else "succeeded"
    if not run.next_node_id:
        run.completed_at = now()
        for pending in db.scalars(
            select(RunStep).where(RunStep.run_id == run.id, RunStep.status == "pending")
        ):
            if pending.id != step.id:
                pending.status = "skipped"
    event(
        db,
        run.tenant_id,
        "run.updated",
        run.id,
        status=run.status,
        node_id=step.node_id,
    )


def fail(db, run, step, message, status="failed"):
    run.status = status
    run.error = message
    run.completed_at = now()
    if step:
        step.status = status
        step.error = message
        step.completed_at = now()
    for pending in db.scalars(
        select(RunStep).where(RunStep.run_id == run.id, RunStep.status == "pending")
    ):
        if step is None or pending.id != step.id:
            pending.status = "skipped"
    event(db, run.tenant_id, "run.updated", run.id, status=status)


def advance_one(db) -> bool:
    run = db.scalar(
        select(WorkflowRun)
        .where(WorkflowRun.status == "queued")
        .order_by(WorkflowRun.started_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if run is None:
        return False
    step = db.scalar(
        select(RunStep).where(
            RunStep.run_id == run.id, RunStep.node_id == run.next_node_id
        )
    )
    try:
        can_execute(db, run)
        graph = owned(db, WorkflowVersion, run.tenant_id, run.version_id).graph_json
        node = next(n for n in graph["nodes"] if n["id"] == run.next_node_id)
        if step is None:
            raise ValueError("Run step is missing")
        step.started_at = now()
        step.input_json = deepcopy(run.context_json["data"])
        kind, cfg = node["type"], node["config"]
        output, port = {}, "out"
        if kind.endswith("_trigger"):
            output = deepcopy(run.context_json["input"])
        elif kind == "data_map":
            output = render(cfg["fields"], run.context_json)
        elif kind == "if_else":
            try:
                value = lookup(cfg["field"], run.context_json)
            except ValueError:
                if cfg["operator"] != "exists":
                    raise
                value = None
            condition = (
                value is not None
                if cfg["operator"] == "exists"
                else (
                    str(value) == cfg["value"]
                    if cfg["operator"] == "equals"
                    else cfg["value"].casefold() in str(value).casefold()
                )
            )
            port = "true" if condition else "false"
            output = {"condition": condition}
        elif kind == "ai_agent":
            snapshot = node["agent_snapshot"]
            secret = (
                None
                if run.mode == "dry_run"
                else get_secret(
                    db, run.tenant_id, snapshot["credential_id"], "openrouter"
                )
            )
            output = agent_reply(
                snapshot,
                str(run.context_json["data"].get("body", run.input_preview)),
                secret,
                run.mode == "dry_run",
            )
        elif kind == "human_approval":
            target = next_node(graph, node["id"])
            action = next(n for n in graph["nodes"] if n["id"] == target)
            snapshot = action_snapshot(db, run, action)
            db.add(
                Approval(
                    tenant_id=run.tenant_id,
                    run_id=run.id,
                    node_id=node["id"],
                    snapshot=snapshot,
                    snapshot_hash=digest(snapshot),
                )
            )
            step.status = "waiting_human"
            run.status = "waiting_human"
            event(db, run.tenant_id, "approval.requested", run.id, status=run.status)
            db.commit()
            return True
        elif kind in ("telegram_send", "record_action"):
            snapshot = action_snapshot(db, run, node)
            previous = [
                e["source"] for e in graph["edges"] if e["target"] == node["id"]
            ]
            approval = db.scalar(
                select(Approval).where(
                    Approval.run_id == run.id,
                    Approval.node_id.in_(previous),
                    Approval.status == "approved",
                )
            )
            if kind == "telegram_send" and (
                approval is None or approval.snapshot_hash != digest(snapshot)
            ):
                raise ValueError(
                    "Approval is missing or the action changed; start a new run for a fresh approval"
                )
            if approval and approval.snapshot_hash != digest(snapshot):
                raise ValueError("Approved action has changed")
            if kind == "telegram_send" and run.mode == "live":
                # Validate access before enqueue and once again immediately before dispatch.
                get_secret(db, run.tenant_id, snapshot["credential_id"], "telegram")
                db.add(
                    Delivery(
                        tenant_id=run.tenant_id,
                        run_id=run.id,
                        node_id=node["id"],
                        snapshot=snapshot,
                    )
                )
                step.status = "waiting_delivery"
                run.status = "waiting_delivery"
                event(db, run.tenant_id, "delivery.queued", run.id, status=run.status)
                db.commit()
                return True
            output = {
                "text": snapshot["text"],
                "simulated": run.mode == "dry_run",
                "sent": False,
                "recorded": kind == "record_action",
            }
        else:
            raise ValueError("Unsupported node handler")
        if len(__import__("json").dumps(output)) > 100_000:
            raise ValueError("Node output is too large")
        finish_step(db, run, step, output, graph, port)
    except Exception as exc:
        from fastapi import HTTPException

        message = (
            str(exc)
            if isinstance(exc, ValueError)
            else (
                "A referenced resource is unavailable"
                if isinstance(exc, HTTPException)
                else "Node execution failed; check its configuration"
            )
        )
        fail(db, run, step, message)
    db.commit()
    return True


def dispatch_one(db) -> bool:
    # All mutations lock the run before child rows, including cancel and approval.
    run = db.scalar(
        select(WorkflowRun)
        .join(Delivery, Delivery.run_id == WorkflowRun.id)
        .where(Delivery.status == "pending")
        .order_by(Delivery.created_at)
        .with_for_update(of=WorkflowRun, skip_locked=True)
        .limit(1)
    )
    if run is None:
        return False
    delivery = db.scalar(
        select(Delivery)
        .where(Delivery.run_id == run.id, Delivery.status == "pending")
        .with_for_update()
    )
    step = db.scalar(
        select(RunStep).where(
            RunStep.run_id == run.id, RunStep.node_id == delivery.node_id
        )
    )
    try:
        can_execute(db, run)
        if run.status != "waiting_delivery":
            raise ValueError("Run is no longer waiting for delivery")
        snapshot = delivery.snapshot
        connection = owned(db, Connection, run.tenant_id, snapshot["connection_id"])
        if (
            connection.status != "active"
            or connection.credential_ref != "vault:" + snapshot["credential_id"]
        ):
            raise ValueError("Telegram connection changed after approval")
        token = get_secret(db, run.tenant_id, snapshot["credential_id"], "telegram")
    except Exception:
        delivery.status = "cancelled"
        delivery.error = "Delivery permission or credential is no longer valid"
        fail(db, run, step, delivery.error)
        db.commit()
        return True
    delivery.status = "dispatching"
    delivery.dispatched_at = now()
    db.commit()  # Durable intent precedes external IO. A crash from here is NEVER blindly retried.
    try:
        receipt = telegram(
            token,
            "sendMessage",
            {"chat_id": snapshot["chat_id"], "text": snapshot["text"]},
        )
        if "message_id" not in receipt:
            raise DeliveryUnknown("Telegram did not return a message receipt")
        delivery.status = "sent"
        delivery.provider_message_id = str(receipt["message_id"])
        graph = owned(db, WorkflowVersion, run.tenant_id, run.version_id).graph_json
        finish_step(
            db,
            run,
            step,
            {
                "sent": True,
                "message_id": delivery.provider_message_id,
                "text": snapshot["text"],
            },
            graph,
        )
    except DeliveryUnknown as exc:
        delivery.status = "delivery_unknown"
        delivery.error = str(exc)
        fail(db, run, step, str(exc), "delivery_unknown")
    except ProviderFailure as exc:
        delivery.status = "failed"
        delivery.error = str(exc)
        fail(db, run, step, str(exc))
    except Exception:
        delivery.status = "delivery_unknown"
        delivery.error = "No reliable delivery receipt; reconcile with Telegram"
        fail(db, run, step, delivery.error, "delivery_unknown")
    db.commit()
    return True


def recover_dispatches(db):
    stale = list(
        db.scalars(
            select(WorkflowRun)
            .join(Delivery, Delivery.run_id == WorkflowRun.id)
            .where(
                Delivery.status == "dispatching",
                Delivery.dispatched_at < now() - timedelta(seconds=90),
            )
            .with_for_update(of=WorkflowRun, skip_locked=True)
            .limit(20)
        )
    )
    for run in stale:
        delivery = db.scalar(
            select(Delivery)
            .where(Delivery.run_id == run.id, Delivery.status == "dispatching")
            .with_for_update()
        )
        delivery.status = "delivery_unknown"
        delivery.error = (
            "Worker stopped while sending; reconcile with Telegram before any new send"
        )
        step = db.scalar(
            select(RunStep).where(
                RunStep.run_id == run.id, RunStep.node_id == delivery.node_id
            )
        )
        fail(db, run, step, delivery.error, "delivery_unknown")
    if stale:
        db.commit()
    return len(stale)
