from datetime import UTC, datetime
import json
import urllib.error
import urllib.request

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.lite.models import (
    AgentProfile,
    Connection,
    InboundMessage,
    LiteWorkflow,
    LiteWorkflowRun,
)


def tenant_connections(db: Session, tenant_id):
    return list(
        db.scalars(
            select(Connection)
            .where(Connection.tenant_id == tenant_id)
            .order_by(Connection.name.asc())
        )
    )


def tenant_messages(db: Session, tenant_id, limit: int = 50):
    return list(
        db.scalars(
            select(InboundMessage)
            .where(InboundMessage.tenant_id == tenant_id)
            .order_by(InboundMessage.received_at.desc())
            .limit(limit)
        )
    )


def tenant_agents(db: Session, tenant_id):
    return list(
        db.scalars(
            select(AgentProfile)
            .where(AgentProfile.tenant_id == tenant_id)
            .order_by(AgentProfile.name.asc())
        )
    )


def tenant_workflows(db: Session, tenant_id):
    return list(
        db.scalars(
            select(LiteWorkflow)
            .where(LiteWorkflow.tenant_id == tenant_id)
            .order_by(LiteWorkflow.updated_at.desc())
        )
    )


def tenant_runs(db: Session, tenant_id, limit: int = 50):
    return list(
        db.scalars(
            select(LiteWorkflowRun)
            .where(LiteWorkflowRun.tenant_id == tenant_id)
            .order_by(LiteWorkflowRun.started_at.desc())
            .limit(limit)
        )
    )


def overview(db: Session, tenant_id):
    connections = tenant_connections(db, tenant_id)
    agents = tenant_agents(db, tenant_id)
    workflows = tenant_workflows(db, tenant_id)
    runs = tenant_runs(db, tenant_id, 500)

    today = datetime.now(UTC).date()
    messages = tenant_messages(db, tenant_id, 500)
    messages_today = [
        item
        for item in messages
        if item.received_at.replace(tzinfo=item.received_at.tzinfo or UTC).date()
        == today
    ]
    channel_counts: dict[str, int] = {}
    for message in messages_today:
        channel_counts[message.channel] = channel_counts.get(message.channel, 0) + 1

    return {
        "connections_total": len(connections),
        "connections_active": sum(1 for item in connections if item.status == "active"),
        "messages_today": len(messages_today),
        "agents_total": len(agents),
        "workflows_total": len(workflows),
        "runs_total": len(runs),
        "runs_success": sum(1 for item in runs if item.status == "success"),
        "channel_counts": channel_counts,
    }


def test_telegram_token(token: str | None) -> dict:
    if not token:
        return {
            "configured": False,
            "connected": False,
            "bot_username": None,
            "bot_name": None,
            "message": "TELEGRAM_BOT_TOKEN chưa được cấu hình trên server.",
        }

    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/getMe",
        headers={"User-Agent": "Flowvia-Lite/0.2"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "configured": True,
            "connected": False,
            "bot_username": None,
            "bot_name": None,
            "message": f"Không thể xác minh Telegram Bot API: {type(exc).__name__}",
        }

    result = payload.get("result") or {}
    return {
        "configured": True,
        "connected": bool(payload.get("ok")),
        "bot_username": result.get("username"),
        "bot_name": result.get("first_name"),
        "message": (
            "Telegram Bot API đã kết nối."
            if payload.get("ok")
            else "Telegram Bot API từ chối token."
        ),
    }
