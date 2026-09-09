# Contracts

Các JSON là đặc tả mẫu, không chứa token và chưa có engine thực thi. `workflow.schema.json` kiểm tra envelope; publish validator còn phải tra registry, schema input/config/output, ports, ancestor mapping, cycle, quyền và budgets. `node-manifest.example.json` minh họa hr.evaluate v1, không đại diện toàn bộ registry.

Workflow HR mẫu kết thúc ở node không có edge được chọn: duplicate=true, approval=rejected/expired, review queue và email. Nhánh review có nhiều incoming dùng first-active semantics. Lỗi không đi qua edge minh họa: runtime policy ghi failed/needs_review. Manifest/action.email tương lai phải nhận approval_ref và resolve snapshot server-side, không tin một boolean approved do client truyền. Demo IDs/credentials phải thay bằng resources cùng tenant trước live run. Schema không thay thế kiểm tra ngữ nghĩa.
