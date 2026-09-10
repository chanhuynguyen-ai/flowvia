from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.modules.identity.dependencies import AuthContext, require_auth, require_csrf
from app.modules.lite.schemas import (
    AgentResponse,
    ConnectionResponse,
    MessageResponse,
    OverviewResponse,
    TelegramTestResponse,
    WorkflowResponse,
    WorkflowRunResponse,
)
from app.modules.lite.service import (
    overview,
    tenant_agents,
    tenant_connections,
    tenant_messages,
    tenant_runs,
    tenant_workflows,
    test_telegram_token,
)

router = APIRouter(prefix="/lite", tags=["lite"])


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    return overview(db, context.membership.tenant_id)


@router.get("/connections", response_model=list[ConnectionResponse])
def get_connections(
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    return tenant_connections(db, context.membership.tenant_id)


@router.post("/connections/telegram/test", response_model=TelegramTestResponse)
def test_telegram_connection(
    context: AuthContext = Depends(require_csrf),
    settings: Settings = Depends(get_settings),
):
    from app.modules.workflows.service import require_role

    require_role(context, "owner")
    return {
        "configured": False,
        "connected": False,
        "message": "Use the tenant-scoped /connections/{id}/test endpoint.",
    }


@router.get("/inbox", response_model=list[MessageResponse])
def get_inbox(
    limit: int = Query(default=50, ge=1, le=200),
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    return tenant_messages(db, context.membership.tenant_id, limit)


@router.get("/agents", response_model=list[AgentResponse])
def get_agents(
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    return tenant_agents(db, context.membership.tenant_id)


@router.get("/workflows", response_model=list[WorkflowResponse])
def get_workflows(
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    return tenant_workflows(db, context.membership.tenant_id)


@router.get("/runs", response_model=list[WorkflowRunResponse])
def get_runs(
    limit: int = Query(default=50, ge=1, le=200),
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
):
    return tenant_runs(db, context.membership.tenant_id, limit)
