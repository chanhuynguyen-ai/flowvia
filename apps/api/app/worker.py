"""Run: python -m app.worker. PostgreSQL is the durable queue for the Lite release."""

import logging
import os
import tempfile
from pathlib import Path
import signal
import time

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.modules.connections.ingress import sync_connection
from app.modules.connections import models as credentials_models  # noqa: F401
from app.modules.executions.engine import advance_one, dispatch_one, recover_dispatches
from app.modules.lite.models import Connection

log = logging.getLogger("flowvia.worker")
logging.getLogger("httpx").setLevel(logging.WARNING)
stopping = False


def stop(*_):
    global stopping
    stopping = True


def main():
    logging.basicConfig(level=logging.INFO)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    last_poll = 0.0
    while not stopping:
        Path(
            os.environ.get(
                "WORKER_HEARTBEAT_FILE",
                str(Path(tempfile.gettempdir()) / "flowvia-worker.heartbeat"),
            )
        ).touch()
        worked = False
        try:
            with SessionLocal() as db:
                recover_dispatches(db)
                worked = dispatch_one(db) or advance_one(db)
            if time.monotonic() - last_poll > 5:
                last_poll = time.monotonic()
                with SessionLocal() as db:
                    ids = list(
                        db.scalars(
                            select(Connection.id).where(
                                Connection.provider == "telegram",
                                Connection.status == "active",
                            )
                        )
                    )
                for ident in ids:
                    if stopping:
                        break
                    with SessionLocal() as db:
                        connection = db.scalar(
                            select(Connection)
                            .where(Connection.id == ident)
                            .with_for_update(skip_locked=True)
                        )
                        if connection and connection.config.get("polling"):
                            try:
                                sync_connection(db, connection)
                            except Exception:
                                db.rollback()
                                log.warning(
                                    "Telegram sync failed for connection %s; retry in the next polling cycle",
                                    ident,
                                )
        except Exception:
            log.error(
                "Worker transaction failed; rolling back and retrying pending work"
            )
        if not worked:
            time.sleep(get_settings().worker_poll_seconds)


if __name__ == "__main__":
    main()
