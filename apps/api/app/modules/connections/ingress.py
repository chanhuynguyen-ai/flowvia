from datetime import UTC, datetime
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.modules.connections.providers import telegram
from app.modules.connections.vault import get_secret
from app.modules.lite.models import Connection, InboundMessage, LiteWorkflow
from app.modules.workflows.models import WorkflowVersion
from app.modules.workflows.service import enqueue, event


def ingest_update(db, connection, update):
    raw = update.get("message") or {}
    if (
        not isinstance(raw, dict)
        or not raw.get("text")
        or raw.get("from", {}).get("is_bot")
    ):
        return None, False
    external_id = str(update["update_id"])
    existing = db.scalar(
        select(InboundMessage).where(
            InboundMessage.connection_id == connection.id,
            InboundMessage.external_message_id == external_id,
        )
    )
    if existing:
        return existing, False
    sender = raw.get("from", {})
    message = InboundMessage(
        tenant_id=connection.tenant_id,
        connection_id=connection.id,
        channel="telegram",
        external_thread_id=str(raw["chat"]["id"]),
        external_message_id=external_id,
        sender_name=(sender.get("first_name") or "Telegram user")[:180],
        sender_handle=(
            ("@" + sender["username"])[:180] if sender.get("username") else None
        ),
        body=raw["text"][:12000],
        status="new",
        received_at=datetime.now(UTC),
        metadata_json={"demo": False},
    )
    try:
        with db.begin_nested():
            db.add(message)
            db.flush()
    except IntegrityError:
        return (
            db.scalar(
                select(InboundMessage).where(
                    InboundMessage.connection_id == connection.id,
                    InboundMessage.external_message_id == external_id,
                )
            ),
            False,
        )
    event(db, connection.tenant_id, "message.received", message.id)
    for workflow in db.scalars(
        select(LiteWorkflow).where(
            LiteWorkflow.tenant_id == connection.tenant_id,
            LiteWorkflow.enabled.is_(True),
        )
    ):
        version = db.scalar(
            select(WorkflowVersion).where(
                WorkflowVersion.workflow_id == workflow.id,
                WorkflowVersion.number == workflow.active_version,
            )
        )
        if version is None:
            continue
        trigger = next(
            (
                n
                for n in version.graph_json["nodes"]
                if n["type"] == "telegram_trigger"
                and n["config"].get("connection_id") == str(connection.id)
            ),
            None,
        )
        if trigger:
            payload = {
                "body": message.body,
                "sender_name": message.sender_name,
                "chat_id": message.external_thread_id,
                "message_id": str(message.id),
            }
            try:
                enqueue(
                    db,
                    workflow,
                    version.created_by,
                    workflow.execution_mode,
                    payload,
                    f"telegram:{connection.id}:{external_id}:{workflow.id}",
                    version.id,
                )
            except Exception as exc:
                from fastapi import HTTPException

                if not isinstance(exc, (HTTPException, ValueError)):
                    raise
                # Keep the message even if the subscription's permissions were revoked.
                event(
                    db,
                    connection.tenant_id,
                    "ingress.blocked",
                    message.id,
                    workflow_id=str(workflow.id),
                )
    return message, True


def sync_connection(db, connection):
    token = get_secret(
        db,
        connection.tenant_id,
        (connection.credential_ref or "").removeprefix("vault:"),
        "telegram",
    )
    updates = telegram(
        token,
        "getUpdates",
        {
            "offset": connection.config.get("offset", 0),
            "limit": 30,
            "timeout": 0,
            "allowed_updates": ["message"],
        },
    )
    count, offset = 0, connection.config.get("offset", 0)
    for update in updates:
        _, created = ingest_update(db, connection, update)
        count += int(created)
        offset = max(offset, int(update["update_id"]) + 1)
    connection.config = {**connection.config, "offset": offset}
    connection.last_checked_at = datetime.now(UTC)
    db.commit()  # Persist messages and offset together before acknowledging the next batch.
    return count
