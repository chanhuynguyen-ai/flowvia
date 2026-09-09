from dataclasses import dataclass
from datetime import UTC, datetime
import hmac

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.identity.models import AuthSession, Membership, User
from app.modules.identity.security import hash_token
from app.modules.identity.service import get_membership

SESSION_COOKIE_NAME = "flowvia_session"
CSRF_COOKIE_NAME = "flowvia_csrf"


@dataclass(frozen=True)
class AuthContext:
    user: User
    membership: Membership
    auth_session: AuthSession


def require_auth(
    flowvia_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> AuthContext:
    if not flowvia_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    auth_session = db.scalar(
        select(AuthSession).where(AuthSession.token_hash == hash_token(flowvia_session))
    )
    now = datetime.now(UTC)
    if (
        auth_session is None
        or auth_session.revoked_at is not None
        or auth_session.expires_at.replace(tzinfo=auth_session.expires_at.tzinfo or UTC) <= now
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    user = db.get(User, auth_session.user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    membership = get_membership(db, user.id, auth_session.current_tenant_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access revoked")

    return AuthContext(user=user, membership=membership, auth_session=auth_session)


def require_csrf(
    context: AuthContext = Depends(require_auth),
    x_csrf_token: str | None = Header(default=None),
    flowvia_csrf: str | None = Cookie(default=None),
) -> AuthContext:
    if not x_csrf_token or not flowvia_csrf or not hmac.compare_digest(x_csrf_token, flowvia_csrf):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
    if not hmac.compare_digest(hash_token(x_csrf_token), context.auth_session.csrf_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
    return context
