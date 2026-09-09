"""Idempotent synthetic seed data for local development only."""

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.modules.identity.models import Membership, Tenant, User
from app.modules.identity.security import hash_password, normalize_email

DEMO_USERS = [
    ("owner@flowvia.local", "FlowviaOwner123!", "Demo Owner"),
    ("builder@flowvia.local", "FlowviaBuilder123!", "Demo Builder"),
    ("reviewer@flowvia.local", "FlowviaReviewer123!", "Demo Reviewer"),
    ("viewer@flowvia.local", "FlowviaViewer123!", "Demo Viewer"),
]


def _get_or_create_user(db, email: str, password: str, display_name: str) -> User:
    normalized = normalize_email(email)
    user = db.scalar(select(User).where(User.email == normalized))
    if user is None:
        user = User(
            email=normalized,
            display_name=display_name,
            password_hash=hash_password(password),
            status="active",
        )
        db.add(user)
        db.flush()
    return user


def seed() -> None:
    settings = get_settings()
    if not settings.seed_demo_data:
        print("SEED_DEMO_DATA is false; skipping synthetic demo seed.")
        return

    with SessionLocal() as db:
        users = {
            email: _get_or_create_user(db, email, password, display_name)
            for email, password, display_name in DEMO_USERS
        }
        owner = users["owner@flowvia.local"]

        personal = db.scalar(
            select(Tenant).where(Tenant.name == "Personal Demo", Tenant.owner_user_id == owner.id)
        )
        if personal is None:
            personal = Tenant(
                name="Personal Demo",
                kind="personal",
                timezone=settings.workspace_default_timezone,
                owner_user_id=owner.id,
                status="active",
            )
            db.add(personal)
            db.flush()

        team = db.scalar(
            select(Tenant).where(Tenant.name == "Flowvia Demo Team", Tenant.owner_user_id == owner.id)
        )
        if team is None:
            team = Tenant(
                name="Flowvia Demo Team",
                kind="team",
                timezone=settings.workspace_default_timezone,
                owner_user_id=owner.id,
                status="active",
            )
            db.add(team)
            db.flush()

        memberships = [
            (personal, owner, "owner"),
            (team, owner, "owner"),
            (team, users["builder@flowvia.local"], "builder"),
            (team, users["reviewer@flowvia.local"], "reviewer"),
            (team, users["viewer@flowvia.local"], "viewer"),
        ]
        for tenant, user, role in memberships:
            exists = db.scalar(
                select(Membership).where(
                    Membership.tenant_id == tenant.id,
                    Membership.user_id == user.id,
                )
            )
            if exists is None:
                db.add(
                    Membership(
                        tenant_id=tenant.id,
                        user_id=user.id,
                        role=role,
                        status="active",
                    )
                )
        db.commit()

    print("Seeded Flowvia synthetic demo users/workspaces (idempotent).")


if __name__ == "__main__":
    seed()
