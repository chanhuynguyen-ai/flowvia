"""Idempotent synthetic inputs and runnable templates; never fabricate execution history."""

from datetime import UTC, datetime
from sqlalchemy import select
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.modules.identity.models import Tenant
from app.modules.lite.models import (
    AgentProfile,
    Connection,
    InboundMessage,
    LiteWorkflow,
)
from app.modules.workflows.service import publish


def node(ident, kind, name, x, y=160, **config):
    return {
        "id": ident,
        "type": kind,
        "label": name,
        "x": x,
        "y": y,
        "config": config,
        "version": "1",
    }


def edge(source, target, port="out"):
    return {"source": source, "target": target, "source_handle": port}


def seed():
    settings = get_settings()
    if not settings.seed_demo_data:
        print("Synthetic product seed is disabled.")
        return
    if settings.app_env == "production":
        raise ValueError("Demo seed cannot run in production")
    with SessionLocal() as db:
        # Restrict automatic demo data to the explicit development workspaces.
        tenants = list(
            db.scalars(
                select(Tenant).where(
                    Tenant.name.in_(["Personal Demo", "Flowvia Demo Team"])
                )
            )
        )
        for tenant in tenants:
            for slug, provider, name in [
                ("telegram-primary", "telegram", "My Telegram bot"),
                ("gmail-primary", "email", "Gmail"),
                ("messenger-primary", "messenger", "Messenger"),
                ("zalo-primary", "zalo", "Zalo OA"),
                ("instagram-output", "instagram", "Instagram"),
            ]:
                conn = db.scalar(
                    select(Connection).where(
                        Connection.tenant_id == tenant.id, Connection.slug == slug
                    )
                )
                if conn is None:
                    conn = Connection(
                        tenant_id=tenant.id,
                        slug=slug,
                        provider=provider,
                        name=name,
                        status="needs_setup" if provider == "telegram" else "planned",
                        config={},
                    )
                    db.add(conn)
                    db.flush()
                if provider == "telegram":
                    telegram = conn
            agent = db.scalar(
                select(AgentProfile).where(
                    AgentProfile.tenant_id == tenant.id,
                    AgentProfile.slug == "support-router",
                )
            )
            if agent is None:
                agent = AgentProfile(
                    tenant_id=tenant.id,
                    slug="support-router",
                    name="Inbox assistant",
                    description="Tóm tắt tin nhắn và soạn phản hồi để bạn duyệt.",
                    model="",
                    provider="openrouter",
                    status="demo",
                    system_prompt="Bạn là trợ lý hỗ trợ khách hàng. Trả lời lịch sự, ngắn gọn bằng tiếng Việt. Nếu chưa đủ thông tin, hãy hỏi lại. Không tự đưa ra cam kết hoặc quyết định tuyển dụng.",
                )
                db.add(agent)
                db.flush()
            templates = [
                (
                    "core-approval-demo",
                    "Core · review & record",
                    "Manual trigger, field mapping, condition, persistent approval and a recorded result.",
                    {
                        "schema_version": 1,
                        "nodes": [
                            node("start", "manual_trigger", "Manual trigger", 50),
                            node(
                                "map",
                                "data_map",
                                "Edit fields",
                                340,
                                fields={"text": "{{ input.body }}"},
                            ),
                            node(
                                "condition",
                                "if_else",
                                "Has a message?",
                                630,
                                field="data.text",
                                operator="exists",
                                value="",
                            ),
                            node("review", "human_approval", "Review result", 920),
                            node(
                                "record",
                                "record_action",
                                "Record result",
                                1210,
                                text="{{ data.text }}",
                            ),
                            node(
                                "empty",
                                "record_action",
                                "No message",
                                920,
                                380,
                                text="No input message",
                            ),
                        ],
                        "edges": [
                            edge("start", "map"),
                            edge("map", "condition"),
                            edge("condition", "review", "true"),
                            edge("condition", "empty", "false"),
                            edge("review", "record"),
                        ],
                    },
                ),
                (
                    "telegram-assistant-v1",
                    "Telegram · message assistant",
                    "Receive a message, draft a reply, review it and send to Telegram.",
                    {
                        "schema_version": 1,
                        "nodes": [
                            node(
                                "trigger",
                                "telegram_trigger",
                                "New Telegram message",
                                60,
                                connection_id=str(telegram.id),
                            ),
                            node(
                                "agent",
                                "ai_agent",
                                "Inbox assistant",
                                370,
                                agent_id=str(agent.id),
                            ),
                            node("approval", "human_approval", "Review reply", 680),
                            node(
                                "send",
                                "telegram_send",
                                "Send to Telegram",
                                990,
                                connection_id=str(telegram.id),
                                chat_id="{{ input.chat_id }}",
                                text="{{ data.reply }}",
                            ),
                        ],
                        "edges": [
                            edge("trigger", "agent"),
                            edge("agent", "approval"),
                            edge("approval", "send"),
                        ],
                    },
                ),
            ]
            for slug, name, description, graph in templates:
                existing = db.scalar(
                    select(LiteWorkflow).where(
                        LiteWorkflow.tenant_id == tenant.id, LiteWorkflow.slug == slug
                    )
                )
                if existing is None:
                    w = LiteWorkflow(
                        tenant_id=tenant.id,
                        slug=slug,
                        name=name,
                        description=description,
                        graph_json=graph,
                        active_version=0,
                        status="draft",
                    )
                    db.add(w)
                    db.flush()
                    publish(db, w, tenant.owner_user_id)
            if (
                db.scalar(
                    select(InboundMessage.id)
                    .where(InboundMessage.tenant_id == tenant.id)
                    .limit(1)
                )
                is None
            ):
                for name, body in [
                    (
                        "Minh Anh",
                        "Bên mình có thể gom tin nhắn từ nhiều kênh vào một nơi không?",
                    ),
                    ("An Nguyễn", "Mình muốn tìm hiểu về gói dịch vụ cho nhóm nhỏ."),
                    ("Khánh", "Cho mình xin thông tin trước khi đăng ký nhé."),
                ]:
                    db.add(
                        InboundMessage(
                            tenant_id=tenant.id,
                            channel="manual",
                            sender_name=name,
                            body=body,
                            status="new",
                            received_at=datetime.now(UTC),
                            external_thread_id="demo-chat",
                            metadata_json={"demo": True},
                        )
                    )
        db.commit()
    print(
        "Prepared demo inputs and runnable templates; execution history starts empty."
    )


if __name__ == "__main__":
    seed()
