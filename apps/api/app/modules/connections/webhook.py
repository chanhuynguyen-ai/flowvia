import hmac
import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.connections.ingress import ingest_update
from app.modules.lite.models import Connection
from app.modules.registry.graph import digest

router = APIRouter(tags=["ingress"])


@router.post("/ingress/telegram/{ident}")
async def webhook(
    ident: uuid.UUID,
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    connection = db.scalar(
        select(Connection).where(Connection.id == ident).with_for_update()
    )
    if (
        connection is None
        or connection.provider != "telegram"
        or connection.status != "active"
    ):
        raise HTTPException(404, "Connection not found")
    expected = connection.config.get("webhook_hash", "")
    if not expected or not hmac.compare_digest(
        expected, digest(x_telegram_bot_api_secret_token)
    ):
        raise HTTPException(403, "Invalid Telegram webhook secret")
    try:
        payload = await request.json()
        if not isinstance(payload, dict) or not isinstance(
            payload.get("update_id"), int
        ):
            raise ValueError()
        _, created = ingest_update(db, connection, payload)
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(422, "Invalid Telegram update") from None
    db.commit()
    return {"ok": True, "created": created}
