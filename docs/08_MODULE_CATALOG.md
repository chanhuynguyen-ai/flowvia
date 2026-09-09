# Module catalog và quy chuẩn mở rộng

## Cách dùng
Node type/version tra registry. Manifest khai báo input/output/config schema, ports, required permissions và effect. Runtime kiểm tra schema trước và sau execute. Editor dùng cùng manifest để sinh form. Xem `packages/contracts/node-manifest.example.json` và workflow ví dụ.

| Type (version 1) | Input → Output | Config | Beta/Pro |
|---|---|---|---|
| trigger.manual | payload → payload | sample input | Beta |
| trigger.form | verified submission → payload | form reference | Beta |
| trigger.gmail | verified email → payload | credential/subscription reference | Beta, cần OAuth |
| data.normalize | payload → document/contact/job refs | field map | Beta |
| data.map | input fields → named fields | safe mapping | Beta |
| data.deduplicate | event/contact/file refs → duplicate result | keys/scope | Beta |
| document.extract | file_ref → structured text/evidence | parser config | Beta |
| logic.if | fields → true/false port | typed condition | Beta |
| logic.router | fields → one selected port | ordered cases/default | Beta |
| ai.extract | text → structured fields | schema/model policy | Beta |
| ai.evaluate | profile/criteria → assessment | rubric reference | Beta |
| ai.compose | approved facts → draft | template/tone | Beta |
| human.approval | context → approved/rejected/expired | scope/deadline | Beta |
| action.email | recipient/body → receipt | credential_ref/send_mode | Beta |
| action.record | record → record_ref | entity/action allowlist | Beta |
| scheduling.offer | application → invitation_ref | slot pool | Beta |
| hr.application.upsert | normalized payload → application_ref | job resolution | Beta |
| hr.evaluate | application + criteria → assessment | criteria version | Beta |
| hr.status.update | application/status → result | allowed transition | Beta |
| hr.review.queue | assessment → task_ref | reviewer scope | Beta |
| flow.subworkflow | mapped payload → child result | pinned child version | Pro |
| logic.join/parallel/loop | branches/items → outputs | explicit semantics/budgets | Pro |
| trigger.schedule | scheduled instant → event | timezone/cron policy | Sau beta cơ bản |

Manifest mẫu dùng hr.evaluate để minh họa module chuyên biệt. Catalog là kế hoạch, không phải registry đã chạy.

## Execution protocol dự kiến
`execute(context, validated_input, validated_config) -> NodeResult(output, selected_port, status)`.
Context có tenant/run/step/attempt/principal/credential resolver giới hạn quyền. Handler không sửa run table trực tiếp; runtime commit output/state/outbox. `waiting` trả wait reference bền vững thay vì giữ thread. AI calls và external effects phải có timeout/budget.
Mapping beta dùng object `{node, path}` hoặc `{literal: value}`; path là field path an toàn, không eval Python/JS. Validator phát hiện node không phải ancestor và trường không có schema. Unknown/null cần policy explicit, không ép thành false/0.

## Quy trình thêm pack mới
Tạo module nghiệp vụ; định nghĩa model/service/permissions; đăng ký manifest/handler; contract tests; template workflow và feature UI nếu cần. Không sửa engine để nhận biết CV hay hóa đơn. Version đã phát hành cần adapter/migration rõ, không sửa hành vi v1 âm thầm.

## Giới hạn beta
DAG tối đa 50 node, Router chọn đúng một nhánh và default bắt buộc; nhiều incoming là first-active, không join. Graph minh họa HR dùng manual trigger với input chuẩn; thay nguồn bằng adapter thực sự sau khi hoàn thành connector. Dry-run chặn tất cả outbound effect. Advanced arbitrary code chưa mở.
