# M1 Foundation Implementation

> Cập nhật 2026-09-10: trạng thái triển khai hiện tại và các gate còn mở được ghi tại [Lite runtime](11_LITE_RUNTIME.md). Nội dung bên dưới giữ thiết kế/hồ sơ của mốc gốc; không dùng để suy ra tính năng đã hoàn thành. Lite hiện dùng PostgreSQL durable worker, chưa dùng Celery.

## Scope implemented

M1 converts the review-only blueprint into the first application slice without changing the platform-first boundary.

### Backend
- FastAPI application with `/health` and DB-backed `/ready`.
- PostgreSQL/SQLAlchemy/Alembic foundation.
- `users`, `tenants`, `memberships`, `auth_sessions` and `outbox_events` schema.
- Personal/team workspace model.
- Opaque web sessions: raw token is sent only to the browser; only SHA-256 is stored in DB.
- Argon2 password hashing.
- HttpOnly session cookie and separate CSRF cookie/header validation for authenticated mutations.
- Current `tenant_id` comes from the authenticated session and active membership.
- Workspace switching checks membership server-side and returns 404 for inaccessible workspace IDs.
- Synthetic local seed accounts only, gated by `SEED_DEMO_DATA=true`.

### Frontend
- React/TypeScript/Vite shell.
- Login state backed by the API.
- Workspace switcher backed by server membership.
- Role-aware navigation shell.
- UI tokens follow `05_UI_UX_GUIDE.md`.
- Screens not implemented in M1 show explicit milestone placeholders instead of fake data/actions.

### Local platform
- Docker Compose now includes PostgreSQL, Redis, MinIO, API and web.
- API container runs migration then idempotent synthetic seed.
- GitHub Actions now checks blueprint, backend tests, PostgreSQL migration/seed and frontend type/build.

## Verified in the preparation environment

Executed from `apps/api`:

```bash
PYTHONPATH=. pytest -q
```

Result: `8 passed`.

Also run from the repository root:

```bash
python scripts/validate_blueprint.py
```

The preparation environment did not provide Docker and had no npm registry network access, so Docker startup and frontend dependency installation/build could not be executed here. CI is configured to perform those checks after push.

## Remaining M1 gates

1. Generate and commit `apps/web/package-lock.json` from the pinned `package.json`, then switch Docker/CI from `npm install` to `npm ci`.
2. Run `docker compose up -d --build` on a machine with Docker and verify:
   - `http://localhost:3000`
   - `http://localhost:8000/health`
   - `http://localhost:8000/ready`
   - login and workspace switch.
3. Preserve the CI run as evidence before moving M1 to Done.

Until those gates pass, roadmap state should remain **In progress**, not Done.

## M2 entry condition

After M1 gates pass, implement the blueprint's core non-HR vertical slice:

`Manual Trigger → Data Map → If/Else → Human Approval → mock Record Action`

The M2 run must persist version/run state in PostgreSQL, survive restart while waiting for approval, pin the published version and execute the approved mock action at most once.
