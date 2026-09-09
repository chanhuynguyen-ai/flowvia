# Implementation Plan

Build vertical slices; mỗi phase sau bootstrap phải giữ ứng dụng runnable.

## Current implementation status — 2026-09-08
- M0 blueprint: prepared.
- Phase 0 source bootstrap: implemented in repository; frontend npm lockfile, Docker startup and CI evidence remain gates.
- Phase 1 backend foundation: config, SQLAlchemy, Alembic, readiness and outbox base implemented; PostgreSQL CI migration is configured.
- Phase 2 identity: **partial** — personal/team workspace, membership, hashed opaque session and CSRF implemented. Full member administration, richer RBAC/scope and credential grants remain.
- Phase 3 frontend shell: **partial** — authenticated React shell, workspace switcher and role-aware navigation implemented; feature routes remain milestone placeholders.
- M2 workflow editor/runtime and all HR/integration phases remain unimplemented.

Do not mark M1 Done until the gates in `09_M1_FOUNDATION.md` pass.

## Phase 0 - Foundation
Hoàn thiện blueprint (đã có); bootstrap React/Vite + FastAPI; dependency lockfiles; local config và Docker app services; health endpoints; CI backend/frontend thực tế.
Acceptance: fresh checkout khởi chạy frontend/API/DB; blueprint validation và basic smoke pass. Compose hiện chỉ hạ tầng, chưa kiểm thử chạy.

## Phase 1 - Backend foundation
Config, SQLAlchemy session, Alembic, health/readiness, structured logging, tenant-scoped base tables, outbox. Acceptance: migration lên DB trống; transaction rollback không phát event.

## Phase 2 - Identity and permissions
Thêm personal/team workspace, cá nhân không cần khai báo công ty; HR pack tùy chọn. Nghiệm thu luồng tạo workflow không HR bên cạnh demo HR.

Session, membership, RBAC/context, CSRF, credential use grants. Acceptance: tenant A không đọc được run/file/HR của tenant B; revoked membership bị từ chối.

## Phase 3 - Frontend shell
React app shell, API client, auth state, protected routes, role-aware nav, UI tokens, trạng thái loading/error. Acceptance: user đăng nhập thấy navigation đúng quyền nhưng backend vẫn bảo vệ request trực tiếp.

## Phase 4 - Core domain model
Workflow/draft/version, registry manifest, schema validators, typed mappings. Canvas thêm/nối/sửa/lưu node. Acceptance: reload giữ graph; incompatible port/cycle/missing input chặn publish; concurrent edit trả conflict.

## Phase 5 - Core business workflow
Runtime bền vững và worker tối thiểu; Manual Trigger → Map → If/Else → Approval → mock Record Action. Chờ duyệt giải phóng worker. Acceptance: restart khi pending, duyệt tiếp đúng một lần; core không import HR; run ghim version cũ khi publish bản mới.
Milestone: low-code vertical slice chạy end-to-end, chưa cần AI. Phần worker/outbox phase 9 phải đưa tối thiểu vào đây vì là dependency của runtime.

## Phase 6 - History, comments and audit
Run inspector, timeline steps/attempts, redacted logs, audit publish/approval/action, notes HR sau khi có HR entity. Acceptance: viewer không thấy secret/PII ngoài scope.

## Phase 7 - Secondary operational workflow
HR pack: jobs, candidates, applications, criteria draft/publish, deterministic filters, dedup và dashboard thô. Form/upload intake; mapping vào HR nodes. Acceptance: cùng người nhiều job không bị gộp đơn; thiếu job được hỏi/duyệt.

## Phase 8 - Attachments/storage
S3/MinIO adapter, validation/quarantine, PDF/DOCX extraction, PDF/Excel criteria draft, signed URLs, failure queue. Acceptance: tệp không đọc được không tự trở thành hồ sơ không đạt; file auth cross-tenant pass. OCR có thể thêm sau với fallback human review.

## Phase 9 - Async jobs and notifications
Mở rộng worker từ phase 5: Gmail OAuth/ingest/send theo quyền thực tế, outbox dispatcher, timeout/backoff, delivery_unknown, retry budgets. Acceptance: event replay và timeout gửi không gây resend mù; dry-run không gửi thật.

## Phase 10 - AI assistance
Provider adapter, schemas, evidence, criteria scoring, bounded conversation, cost limits, evaluation dataset và human review. Acceptance: invalid output/prompt injection không kích hoạt action trái quyền; unknown tách fail; kết quả có criteria/model version. AI nằm trong beta, không chờ Pro.

## Phase 11 - Retrieval/RAG
Không bắt buộc beta. Chỉ triển khai khi có nhu cầu hỏi đáp tri thức công ty; trước đó xác định nguồn, quyền truy cập, evaluation và câu trả lời thiếu bằng chứng.

## Phase 12 - Admin/configuration
Workspace timezone, templates, retention, role/scope, connector health, node permissions; kiểm soát automatic email. Acceptance: chỉnh recipient/content sau approval yêu cầu duyệt lại; export không chứa secret.

## Phase 13 - SLA/scheduling/automation
Slot/booking, token ứng viên, nhắc lịch, approval expiry. Acceptance: tranh slot cuối, expiry, cancel/reschedule và timezone đúng; notification riêng từng ứng viên. Calendar ngoài chỉ khi connector được xác minh.

## Phase 14 - Analytics
Định nghĩa và đối soát tin nhắn/ứng viên/đơn/CV riêng; trạng thái current evaluation, pending approvals, lịch và lỗi gửi. Acceptance: ngày theo timezone workspace, retries không tăng count.

## Phase 15 - Hardening
Permission, recovery, concurrent approval/booking, malicious file, provider outage, backup/restore và benchmark mục tiêu. Beta gate: toàn bộ acceptance ở product spec đạt; lưu bằng chứng kết quả kiểm thử, không chỉ checklist.

## Phase 16 - Deployment and observability
Staging, migrations, secret config, HTTPS, metrics, release/rollback, smoke; production target cần chốt. Không mở connector chưa được phép. Pro sau beta: subworkflow, join/parallel/loop giới hạn, approvals nhiều cấp, environment/quota; business packs mới tái sử dụng core.

## Git strategy
Một thay đổi coherent/branch: feat/platform-foundation, feat/auth-rbac, feat/workflow-editor, feat/workflow-runtime, feat/hr-pack, feat/ai-evaluation. Conventional commits: feat(workflows), fix(approvals), test(tenancy), docs(architecture). Không cần agents song song để dùng sườn này.

## Definition of done for every slice
- [ ] Hành vi end-to-end được triển khai, không chỉ mock UI.
- [ ] Backend/worker authorization và validation.
- [ ] Migration và dữ liệu demo không nhạy cảm.
- [ ] Critical tests về quyền/trạng thái/persistence pass.
- [ ] Docs/contract và trạng thái thực tế được cập nhật.
- [ ] Checkout chạy được theo README.
- [ ] Commit mô tả đúng thay đổi.

## Dependency and milestone summary
M0 blueprint → M1 foundation/auth → M2 canvas + persistent engine + minimal worker → M3 HR/files → M4 real connectors/AI → M5 approvals/email/forms/booking/dashboard hardening → beta. Các phase đánh số giữ theo sườn gốc; dependency worker được đưa sớm vào phase 5 như mô tả trên.
