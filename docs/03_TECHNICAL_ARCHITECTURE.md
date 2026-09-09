# Technical Architecture

## 1. Architecture strategy
Modular monolith, worker tách process nhưng dùng chung domain packages. Ba lớp: platform core → generic node plugins → business packs. Dependency chỉ từ pack sang interface core; registry không hardcode HR. Node graph là dữ liệu, không phải hàm HR cố định.

## 2. Technology stack
| Layer | Choice | Reason |
|---|---|---|
| Frontend | ReactJS, TypeScript, Vite; canvas React Flow dự kiến | React theo yêu cầu, tương tác node/edge |
| Backend | FastAPI/Python | API và domain chính bằng Python |
| Database | PostgreSQL, SQLAlchemy, Alembic | Transaction và version/run bền vững |
| Queue/cache | Celery, Redis | Tác vụ nền; không dùng Redis làm nguồn trạng thái duy nhất |
| Storage | S3-compatible/MinIO local | Tách tệp khỏi DB |
| AI | Provider adapter, structured output | Thay provider, validate và giới hạn chi phí |
| Containers | Docker Compose local/staging | Môi trường phát triển |
| CI/CD | GitHub Actions | M1 jobs: blueprint, backend tests, PostgreSQL migration/seed, frontend type/build |

Các lựa chọn ngoài React/FastAPI/Python là thiết kế đề xuất; cần khóa phiên bản tương thích và kiểm tra tài liệu chính thức khi bootstrap.

## 3. Frontend architecture
`app` chứa shell/router/providers; `features` theo nghiệp vụ; `components` UI chung; `lib` API client; `hooks` hook chung; `types` dùng contract. Canvas hiển thị graph, backend là nguồn xác thực graph và quyền. Cấu hình node sinh từ manifest; widget đặc thù đăng ký riêng.

## 4. Backend architecture
`core`: config, DB, logging, auth dependencies. `shared`: node protocol, schema/mapping, event envelope. `modules`: identity, connections, registry, workflows, executions, approvals, files, notifications, scheduling, analytics, audit, hr.
Module triển khai router/schemas/models/service/repository khi có nhu cầu, không tạo các lớp rỗng chỉ để đủ tên. Node handler nhận RunContext giới hạn quyền và trả output schema; không lấy secret trực tiếp từ JSON graph.

## 5. API design
Base `/api/v1`; UUID; cursor pagination; errors `{code,message,details,request_id}`; 401/403/404/409/422 theo ngữ cảnh. `Idempotency-Key` cho command có tác dụng phụ.
| Resource/command | Purpose |
|---|---|
| GET /modules | Manifest được phép dùng |
| POST /workflows; PATCH /workflows/{id} | Draft với revision/If-Match |
| POST /workflows/{id}/validate | Kiểm tra graph/schema/quyền |
| POST /workflows/{id}/publish | Snapshot version bất biến |
| POST /workflow-versions/{id}/runs | Dry-run hoặc live với input |
| GET /runs/{id}; GET /runs/{id}/steps | Theo dõi trạng thái |
| POST /runs/{id}/cancel | Hủy các bước chưa chạy; không thu hồi email đã gửi |
| POST /approvals/{id}/decide | Approve/reject nguyên tử |
| POST /connections/{id}/test | Kiểm tra credential phía server |
| POST /ingress/{connection_id} | Adapter xác minh sự kiện |
| /hr/jobs; /hr/candidates; /hr/applications | Dữ liệu HR phân quyền |
| POST /hr/criteria/{id}/publish | Xác nhận bộ tiêu chí |
| POST /public/forms/{token}/submit | Nộp dữ liệu giới hạn quyền |
| POST /public/bookings/{token}/reserve | Giữ slot nguyên tử |

## 6. Core domain/state model
Draft sửa được; version published bất biến. Run: queued → running → waiting_human/waiting_input → running → succeeded; nhánh terminal failed/cancelled. Step: pending/running/waiting/succeeded/failed/skipped/cancelled. Mỗi step có attempts riêng; retry không sửa lịch sử attempt.
Beta DAG tuần tự với Router chọn một nhánh; nhiều incoming dùng first-active semantics, không phải join. Nhiều trigger trên canvas được biên dịch thành subscription riêng, mỗi run chỉ có một trigger gốc. Validator giới hạn tối đa 50 node/run, payload JSON 1 MiB, tệp 20 MiB (giới hạn beta đề xuất). Nhánh không chọn marked skipped. Timeout và chi phí AI có budget.
Chờ con người ghi DB và giải phóng worker; sự kiện quyết định đánh thức run. Không giữ process sleep chờ duyệt. Loop/join/subworkflow nâng cao phải có semantics và version mới trước khi mở.

## 7. AI architecture
Allowed: đọc tài liệu, trích xuất, phân loại, đánh giá theo criteria, soạn tin, hỏi thiếu thông tin. Forbidden: cấp quyền, suy đoán đặc điểm cá nhân không liên quan, quyết định tuyển dụng cuối, tự thực thi lệnh trong tài liệu.
Parse thành JSON rồi schema validate; output có evidence/source refs và unknown. Lưu provider/model/prompt version/criteria version/latency/token cost khi có. Không lưu chain-of-thought; chỉ lý do ngắn và bằng chứng. AI không có tool tùy ý; action đi qua node runtime và policy. Provider lỗi chuyển retry có giới hạn rồi human review. Không cần RAG cho beta CV; nếu thêm tri thức công ty cần scope tenant và nguồn xác minh.

## Workspace đa đối tượng
Dùng tenant như workspace, thêm kind personal/team; personal có một Owner, team có memberships. Department/job scopes chỉ áp dụng pack có nhu cầu; không bắt người dùng cá nhân tạo công ty. Dùng cùng engine/node registry và isolation cho mọi loại workspace. Agent composer vẫn tuân thủ action policy và durable execution. Không nhập hoặc thực thi workflow JSON của n8n nếu chưa có adapter được triển khai/kiểm thử.

## 8. Authentication and authorization
Session cookie HttpOnly/Secure/SameSite cho web, CSRF trên mutation; password hashing chuẩn triển khai hoặc OIDC theo quyết định sau. RBAC + resource scope (tenant, department, job, workflow, credential). Worker kiểm tra quyền thực thi của version/service principal; thu hồi credential phải dừng action tiếp theo.

## 9. Database strategy
PostgreSQL là nguồn chuẩn; mọi bảng doanh nghiệp có tenant_id. Composite FK/unique có tenant để tránh liên kết chéo. JSONB cho version graph và output giới hạn; domain trọng yếu lưu typed columns. Alembic cho thay đổi schema. Outbox cùng transaction với domain state.

## 10. Background jobs
Ingest, parse, AI, execute node, dispatch outbox, email, reminder. At-least-once delivery; unique event/action keys. External send timeout sau dispatch → delivery_unknown → đối soát; không khẳng định exactly-once nếu provider không hỗ trợ. Tác vụ hết heartbeat cần recovery với lease/fencing.

## 11. File/object storage
Object key theo tenant và opaque ID; filename gốc chỉ metadata. MIME/signature/size checks, quarantine và scan trước parse; signed URL ngắn hạn sau authorization. Không public bucket. OCR lỗi đưa cần kiểm tra. Retention áp dụng cả bản gốc, extraction và backup theo policy.

## 12. Security
HTTPS production; CORS allowlist; secret manager/encryption; redaction; rate limits; kiểm soát egress/SSRF cho connector; allowlist provider endpoints. Python module do nhà phát triển review; chạy mã người dùng là ngoài beta, cần sandbox độc lập. Prompt injection không được vượt action policy.

## 13. Observability
request_id, tenant_id, run_id, step_id, attempt_id; queue depth, latency, failures, pending approvals, delivery_unknown, AI spend. Không log raw CV/token. Audit mutation quan trọng, log ứng dụng có retention ngắn hơn hồ sơ theo cấu hình.

## 14. Testing strategy
Domain tests cho graph, mapping, criteria; integration PostgreSQL cho transaction, dedup, booking và restart; permission tests API/worker/file; provider contract mocks; E2E từ canvas đến approval. AI evaluation bằng dữ liệu giả/được phép, so với nhãn HR, không chỉ test JSON hợp lệ.

## 15. CI/CD
M1 source configures blueprint validation, backend tests, a PostgreSQL migration/seed job and frontend type/build. The frontend still uses `npm install` until a committed lockfile is generated; therefore M1 is not Done yet. Future gates add lint, stronger integration tests, migration consistency, staging smoke, backup checks and release/rollback evidence.

## 16. Architecture trade-offs
Modular monolith giảm vận hành ban đầu. Runtime beta giới hạn thay vì cố sao chép toàn n8n; vẫn phải bền vững. Nếu yêu cầu long-running orchestration vượt khả năng engine nội bộ, đánh giá engine chuyên dụng trước khi mở rộng. React Flow là lựa chọn dự kiến, không buộc contract phụ thuộc thư viện canvas. Native desktop, microservices và vector DB hoãn đến khi có nhu cầu chứng minh.
