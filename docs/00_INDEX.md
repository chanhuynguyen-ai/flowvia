# Documentation Index

1. `01_PROJECT_OVERVIEW.md` — mục tiêu, phạm vi cá nhân/nhóm/doanh nghiệp và cảm hứng n8n.
2. `02_PRODUCT_SPECIFICATION.md` — tính năng, luật, stories và tiêu chí beta.
3. `03_TECHNICAL_ARCHITECTURE.md` — stack, runtime, API, bảo mật và trade-offs.
4. `04_APPLICATION_FLOW.md` — hành trình, trạng thái và xử lý lỗi.
5. `05_UI_UX_GUIDE.md` — phong cách desktop, canvas, màn hình và accessibility.
6. `06_BACKEND_DATABASE_AUTH.md` — entity, tenant, quyền, transaction và retention.
7. `07_IMPLEMENTATION_PLAN.md` — phases, dependency, milestones và nghiệm thu.
8. `08_MODULE_CATALOG.md` — node catalog, protocol và cách thêm business pack.
9. `09_M1_FOUNDATION.md` — source M1 đã triển khai, verification và gate còn lại.

10. `10_M2_LITE_PRODUCT_PREVIEW.md` — hồ sơ UI preview trước đây.
11. `11_LITE_RUNTIME.md` — triển khai Lite 0.3, hướng dẫn chạy và bằng chứng hiện tại.

## Contracts
- `../packages/contracts/lite-workflow.schema.json`: schema graph Lite 0.3 hiện hành.
- `../packages/contracts/node-manifest.example.json`: manifest module HR mẫu.
- `../packages/contracts/workflow.schema.json`: schema định dạng graph tối thiểu.
- `../packages/contracts/hr-intake.workflow.json`: cấu hình workflow minh họa HR.

## Rule
Cập nhật tài liệu khi quyết định thay đổi. Những thành phần mô tả ở đây là thiết kế cần triển khai; không coi JSON ví dụ là runtime có thể chạy khi chưa viết engine.

## Repository review
- `REVIEWER_GUIDE.md` — available evidence and implementation gaps.
- `ROADMAP.md` — high-level milestones and honest delivery status.
