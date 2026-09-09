import os
from pathlib import Path
import uuid

os.environ["DATABASE_URL"] = "sqlite:///./flowvia_test.db"
os.environ["SESSION_COOKIE_SECURE"] = "false"
os.environ["SESSION_TTL_HOURS"] = "12"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.modules.executions import models as execution_models  # noqa: F401
from app.modules.identity.models import Membership, Tenant, User
from app.modules.identity.security import hash_password

TEST_DB = Path("flowvia_test.db")
engine = create_engine("sqlite:///./flowvia_test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _seed(db: Session) -> dict[str, uuid.UUID]:
    owner = User(
        email="owner@test.local",
        display_name="Test Owner",
        password_hash=hash_password("OwnerTest123!"),
        status="active",
    )
    reviewer = User(
        email="reviewer@test.local",
        display_name="Test Reviewer",
        password_hash=hash_password("ReviewerTest123!"),
        status="active",
    )
    db.add_all([owner, reviewer])
    db.flush()

    personal = Tenant(
        name="Owner Personal",
        kind="personal",
        timezone="Asia/Ho_Chi_Minh",
        status="active",
        owner_user_id=owner.id,
    )
    team = Tenant(
        name="Team Alpha",
        kind="team",
        timezone="Asia/Ho_Chi_Minh",
        status="active",
        owner_user_id=owner.id,
    )
    foreign = Tenant(
        name="Foreign Team",
        kind="team",
        timezone="UTC",
        status="active",
        owner_user_id=reviewer.id,
    )
    db.add_all([personal, team, foreign])
    db.flush()
    db.add_all(
        [
            Membership(tenant_id=personal.id, user_id=owner.id, role="owner", status="active"),
            Membership(tenant_id=team.id, user_id=owner.id, role="owner", status="active"),
            Membership(tenant_id=foreign.id, user_id=reviewer.id, role="owner", status="active"),
        ]
    )
    db.commit()
    return {"owner": owner.id, "personal": personal.id, "team": team.id, "foreign": foreign.id}


@pytest.fixture
def db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestingSessionLocal() as session:
        ids = _seed(session)
        yield session, ids


@pytest.fixture
def client(db):
    def override_get_db():
        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def pytest_sessionfinish(session, exitstatus):
    if TEST_DB.exists():
        TEST_DB.unlink()
