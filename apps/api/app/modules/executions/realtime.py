"""DB backed event replay across API/worker processes and reconnects."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from app.core.config import get_settings
from app.core.database import get_db
from app.modules.executions.models import RuntimeEvent
from app.modules.identity.dependencies import require_auth

router = APIRouter()


@router.websocket("/ws")
async def workspace_events(ws: WebSocket, db: Session = Depends(get_db)):
    settings = get_settings()
    if ws.headers.get("origin") not in set(
        settings.cors_origin_list + [settings.app_url]
    ):
        await ws.close(code=1008)
        return
    token = ws.cookies.get("flowvia_session")
    try:
        context = await run_in_threadpool(require_auth, token, db)
    except HTTPException:
        await ws.close(code=1008)
        return
    tenant_id = context.membership.tenant_id
    try:
        cursor = max(0, int(ws.query_params.get("after", "0")))
    except ValueError:
        await ws.close(code=1008)
        return
    if not cursor:
        cursor = (
            db.scalar(
                select(func.max(RuntimeEvent.id)).where(
                    RuntimeEvent.tenant_id == tenant_id
                )
            )
            or 0
        )
    db.rollback()
    await ws.accept()
    await ws.send_json(
        {"type": "ready", "cursor": cursor, "workspace_id": str(tenant_id)}
    )

    def read_events(after):
        db.rollback()
        db.expire_all()
        current = require_auth(token, db)
        if current.membership.tenant_id != tenant_id:
            raise HTTPException(403, "Workspace changed")
        rows = [
            {"id": e.id, "type": e.topic, "resource_id": e.resource_id, "data": e.data}
            for e in db.scalars(
                select(RuntimeEvent)
                .where(RuntimeEvent.tenant_id == tenant_id, RuntimeEvent.id > after)
                .order_by(RuntimeEvent.id)
                .limit(100)
            )
        ]
        db.rollback()  # Release the connection while this WebSocket waits.
        return rows

    try:
        while True:
            rows = await run_in_threadpool(read_events, cursor)
            for row in rows:
                await ws.send_json(row)
                cursor = row["id"]
            if not rows:
                await ws.send_json({"type": "heartbeat", "cursor": cursor})
            await asyncio.sleep(1)
    except HTTPException:
        await ws.close(code=1008)
    except (WebSocketDisconnect, RuntimeError):
        pass
