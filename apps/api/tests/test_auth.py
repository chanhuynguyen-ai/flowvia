from sqlalchemy import select

from app.modules.identity.models import AuthSession, Membership
from app.modules.identity.security import hash_token


def _login(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@test.local", "password": "OwnerTest123!"},
    )
    assert response.status_code == 200, response.text
    return response


def _csrf(client) -> str:
    token = client.cookies.get("flowvia_csrf")
    assert token
    return token


def test_invalid_password_is_rejected(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@test.local", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "http_401"


def test_login_uses_hashed_session_and_personal_workspace(client, db):
    response = _login(client)
    payload = response.json()
    assert payload["user"]["email"] == "owner@test.local"
    assert payload["current_workspace"]["kind"] == "personal"

    raw_session = client.cookies.get("flowvia_session")
    assert raw_session

    with db[0].bind.connect():
        stored = db[0].scalar(select(AuthSession))
    assert stored is not None
    assert stored.token_hash == hash_token(raw_session)
    assert stored.token_hash != raw_session


def test_switch_workspace_requires_membership_and_csrf(client, db):
    _login(client)
    ids = db[1]

    missing_csrf = client.post(
        "/api/v1/auth/switch-workspace",
        json={"workspace_id": str(ids["team"])},
    )
    assert missing_csrf.status_code == 403

    switched = client.post(
        "/api/v1/auth/switch-workspace",
        json={"workspace_id": str(ids["team"])},
        headers={"X-CSRF-Token": _csrf(client)},
    )
    assert switched.status_code == 200
    assert switched.json()["current_workspace"]["name"] == "Team Alpha"

    foreign = client.post(
        "/api/v1/auth/switch-workspace",
        json={"workspace_id": str(ids["foreign"])},
        headers={"X-CSRF-Token": _csrf(client)},
    )
    assert foreign.status_code == 404


def test_revoked_membership_is_denied_even_with_valid_session(client, db):
    _login(client)
    ids = db[1]
    switched = client.post(
        "/api/v1/auth/switch-workspace",
        json={"workspace_id": str(ids["team"])},
        headers={"X-CSRF-Token": _csrf(client)},
    )
    assert switched.status_code == 200

    session, _ = db
    membership = session.scalar(
        select(Membership).where(
            Membership.tenant_id == ids["team"],
            Membership.user_id == ids["owner"],
        )
    )
    membership.status = "revoked"
    session.commit()

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 403


def test_logout_revokes_session(client):
    _login(client)
    response = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": _csrf(client)},
    )
    assert response.status_code == 204

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401
