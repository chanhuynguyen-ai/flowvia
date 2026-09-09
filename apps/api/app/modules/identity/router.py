from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.modules.identity.dependencies import (
    CSRF_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    AuthContext,
    require_auth,
    require_csrf,
)
from app.modules.identity.schemas import LoginRequest, SessionResponse, SwitchWorkspaceRequest
from app.modules.identity.service import (
    authenticate,
    build_session_response,
    create_auth_session,
    get_membership,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(
    response: Response,
    session_token: str,
    csrf_token: str,
    settings: Settings,
) -> None:
    max_age = settings.session_ttl_hours * 60 * 60
    common = {
        "secure": settings.session_cookie_secure,
        "samesite": "lax",
        "max_age": max_age,
        "path": "/",
    }
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_token,
        httponly=True,
        **common,
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        httponly=False,
        **common,
    )


@router.post("/login", response_model=SessionResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SessionResponse:
    user = authenticate(db, payload.email, payload.password)
    auth_session, session_token, csrf_token = create_auth_session(db, user, settings)
    _set_auth_cookies(response, session_token, csrf_token, settings)
    return build_session_response(db, user, auth_session.current_tenant_id)


@router.get("/me", response_model=SessionResponse)
def me(
    context: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db),
) -> SessionResponse:
    return build_session_response(db, context.user, context.auth_session.current_tenant_id)


@router.post("/switch-workspace", response_model=SessionResponse)
def switch_workspace(
    payload: SwitchWorkspaceRequest,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> SessionResponse:
    membership = get_membership(db, context.user.id, payload.workspace_id)
    if membership is None:
        # Avoid disclosing whether another workspace exists.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    context.auth_session.current_tenant_id = membership.tenant_id
    db.commit()
    return build_session_response(db, context.user, membership.tenant_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> Response:
    context.auth_session.revoked_at = datetime.now(UTC)
    db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
