from datetime import UTC, datetime

from app.modules.lite.models import (
    AgentProfile,
    Connection,
    InboundMessage,
    LiteWorkflow,
    LiteWorkflowRun,
)


def _login(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@test.local", "password": "OwnerTest123!"},
    )
    assert response.status_code == 200


def _csrf(client) -> str:
    token = client.cookies.get("flowvia_csrf")
    assert token
    return token


def test_lite_endpoints_are_tenant_scoped(client, db):
    session, ids = db
    workflow = LiteWorkflow(
        tenant_id=ids["personal"],
        slug="test-flow",
        name="Test Flow",
        description="tenant scoped",
        status="draft",
        active_version=1,
        graph_json={"nodes": [], "edges": []},
    )
    foreign_workflow = LiteWorkflow(
        tenant_id=ids["foreign"],
        slug="foreign-flow",
        name="Foreign Flow",
        description="must not leak",
        status="draft",
        active_version=1,
        graph_json={"nodes": [], "edges": []},
    )
    session.add_all([workflow, foreign_workflow])
    session.flush()

    connection = Connection(
        tenant_id=ids["personal"],
        slug="telegram",
        provider="telegram",
        name="Telegram",
        status="needs_setup",
        credential_ref="env:TELEGRAM_BOT_TOKEN",
        config={},
    )
    agent = AgentProfile(
        tenant_id=ids["personal"],
        slug="router",
        name="Router",
        description="demo",
        provider="openrouter",
        model="demo/model",
        system_prompt="demo",
        status="ready",
    )
    session.add_all([connection, agent])
    session.flush()
    session.add(
        InboundMessage(
            tenant_id=ids["personal"],
            connection_id=connection.id,
            channel="telegram",
            sender_name="Demo",
            sender_handle="@demo",
            body="hello",
            ai_summary="greeting",
            status="new",
            metadata_json={},
            received_at=datetime.now(UTC),
        )
    )
    session.add(
        LiteWorkflowRun(
            tenant_id=ids["personal"],
            workflow_id=workflow.id,
            status="success",
            trigger_channel="telegram",
            input_preview="hello",
            output_preview="hi",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
    )
    session.commit()

    _login(client)
    workflows = client.get("/api/v1/lite/workflows")
    assert workflows.status_code == 200
    assert [item["name"] for item in workflows.json()] == ["Test Flow"]

    overview = client.get("/api/v1/lite/overview")
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["connections_total"] == 1
    assert payload["messages_today"] == 1
    assert payload["agents_total"] == 1
    assert payload["workflows_total"] == 1
    assert payload["runs_success"] == 1


def test_telegram_test_requires_csrf_and_never_needs_token_in_payload(client):
    _login(client)

    denied = client.post("/api/v1/lite/connections/telegram/test")
    assert denied.status_code == 403

    response = client.post(
        "/api/v1/lite/connections/telegram/test",
        headers={"X-CSRF-Token": _csrf(client)},
    )
    assert response.status_code == 200
    assert response.json()["configured"] is False
    assert response.json()["connected"] is False
