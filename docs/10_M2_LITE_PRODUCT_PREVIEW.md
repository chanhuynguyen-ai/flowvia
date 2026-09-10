# M2 Lite Product Preview

> Cập nhật 2026-09-10: trạng thái triển khai hiện tại và các gate còn mở được ghi tại [Lite runtime](11_LITE_RUNTIME.md). Nội dung bên dưới giữ thiết kế/hồ sơ của mốc gốc; không dùng để suy ra tính năng đã hoàn thành. Lite hiện dùng PostgreSQL durable worker, chưa dùng Celery.

## Product direction
Flowvia Lite is the first customer-facing product slice built on the M1 platform foundation. It focuses on omni-channel conversations routed through AI agents and low-code workflows.

Target interaction:

`Channel input → unified message → agent → workflow logic → channel output`

Telegram is the first real connector target. Email, Meta Messenger, Zalo OA and Instagram remain planned until their credential/runtime boundaries are implemented and verified.

## Implemented in this preview
- Dark business shell inspired by modern AI developer products, without copying a third-party UI.
- Overview metrics backed by tenant-scoped API data.
- Unified Inbox backed by `inbound_messages`.
- Connections catalog backed by `connections`.
- Agent profiles backed by `agent_profiles`.
- Workflow canvas preview backed by `lite_workflows.graph_json`.
- Run history backed by `lite_workflow_runs`.
- Telegram connection health endpoint using `TELEGRAM_BOT_TOKEN` from server environment only.
- Synthetic development seed data marked as demo data.

## Security boundary
- Connector secrets are not stored in workflow JSON or response payloads.
- Telegram uses the credential reference `env:TELEGRAM_BOT_TOKEN` in Lite development mode.
- All Lite read APIs derive `tenant_id` from the authenticated server session.
- Telegram connection test requires CSRF validation.

## Not yet implemented
This preview is not the final M2 durable workflow engine. It intentionally does not claim:
- Telegram webhook ingestion.
- AI provider execution.
- Telegram outbound send.
- immutable workflow publish/version semantics.
- durable worker/restart recovery.
- drag/drop graph persistence or typed port validation.

Those are the next runtime slice after the UI/data model is accepted.

## Next vertical slice
`Telegram webhook → persist message → AI agent → persist run → Telegram send`

The runtime must keep provider tokens out of logs/database, use an idempotency key for Telegram updates/outbound actions, and record a run before performing side effects.

## Preparation verification
Executed in the preparation environment:
- blueprint validator: PASS
- backend tests: 10 passed
- Python compileall: PASS
- Alembic fresh database migration: `20260908_0002 (head)`
- M1 + Lite seed: PASS and idempotent
- Docker Compose YAML structure: 5 services; PostgreSQL has no host port mapping
- TS/TSX syntax transpile check: 15 files, 0 syntax errors

The M2 frontend production build still needs to be executed on the Windows/Docker environment because outbound npm install timed out in the preparation sandbox. The previous M1 Docker build does not count as evidence for the changed M2 frontend.
