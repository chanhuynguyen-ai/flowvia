from datetime import UTC, datetime, timedelta
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.identity.models import AuthSession, Membership, Tenant, User
from app.modules.identity.schemas import SessionResponse, UserSummary, WorkspaceSummary
from app.modules.identity.security import (
    generate_token,
    hash_token,
    normalize_email,
    verify_password,
)


def _active_memberships(db: Session, user_id: uuid.UUID) -> list[Membership]:
    return list(
        db.scalars(
            select(Membership)
            .join(Tenant, Tenant.id == Membership.tenant_id)
            .where(
                Membership.user_id == user_id,
                Membership.status == "active",
                Tenant.status == "active",
            )
        ).all()
    )


def _choose_default_membership(memberships: list[Membership]) -> Membership:
    if not memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active workspace membership")
    return sorted(
        memberships,
        key=lambda membership: (
            0 if membership.tenant.kind == "personal" else 1,
            0 if membership.role == "owner" else 1,
            str(membership.tenant_id),
        ),
    )[0]


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(
        select(User).where(User.email == normalize_email(email), User.status == "active")
    )
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return user


def create_auth_session(
    db: Session,
    user: User,
    settings: Settings,
) -> tuple[AuthSession, str, str]:
    memberships = _active_memberships(db, user.id)
    membership = _choose_default_membership(memberships)
    session_token = generate_token()
    csrf_token = generate_token()
    auth_session = AuthSession(
        user_id=user.id,
        current_tenant_id=membership.tenant_id,
        token_hash=hash_token(session_token),
        csrf_hash=hash_token(csrf_token),
        expires_at=datetime.now(UTC) + timedelta(hours=settings.session_ttl_hours),
    )
    db.add(auth_session)
    db.commit()
    db.refresh(auth_session)
    return auth_session, session_token, csrf_token


def get_membership(
    db: Session,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Membership | None:
    return db.scalar(
        select(Membership)
        .join(Tenant, Tenant.id == Membership.tenant_id)
        .where(
            Membership.user_id == user_id,
            Membership.tenant_id == tenant_id,
            Membership.status == "active",
            Tenant.status == "active",
        )
    )


def build_session_response(
    db: Session,
    user: User,
    current_tenant_id: uuid.UUID,
) -> SessionResponse:
    memberships = _active_memberships(db, user.id)
    current = next((m for m in memberships if m.tenant_id == current_tenant_id), None)
    if current is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access revoked")

    workspaces = [
        WorkspaceSummary(
            id=m.tenant.id,
            name=m.tenant.name,
            kind=m.tenant.kind,
            timezone=m.tenant.timezone,
            role=m.role,
        )
        for m in sorted(memberships, key=lambda item: item.tenant.name.casefold())
    ]
    current_summary = WorkspaceSummary(
        id=current.tenant.id,
        name=current.tenant.name,
        kind=current.tenant.kind,
        timezone=current.tenant.timezone,
        role=current.role,
    )
    return SessionResponse(
        user=UserSummary.model_validate(user),
        current_workspace=current_summary,
        workspaces=workspaces,
    )
