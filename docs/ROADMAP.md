# Roadmap

Tiến độ ngày 2026-09-10. Đây là mốc nghiệm thu, không phải cam kết ngày phát hành.

| Mốc | Phạm vi | Trạng thái |
| --- | --- | --- |
| M0 | Blueprint, contracts, cấu trúc repo | Đã có |
| M1 | React/FastAPI, PostgreSQL, workspace/session | Source và test có; Docker/CI gate còn mở |
| M2 preview | Giao diện và dữ liệu minh họa trong ZIP cũ | Hồ sơ lịch sử, không phải runtime |
| Lite 0.3.0 / M2 | Canvas → publish → worker → approval → action, Telegram/OpenRouter adapters | Đã triển khai; 35 tests và build pass; còn browser/PostgreSQL/live acceptance |
| M3 | HR intake, hồ sơ, tiêu chí, bằng chứng và duyệt | Chưa triển khai |
| M4 | Gmail/Meta/Zalo, forms, email và booking có kiểm soát | Chưa triển khai; Telegram text là tích hợp đầu tiên của Lite |
| M5 | Public beta: onboarding, quota, retention, reliability, vận hành | Chưa nghiệm thu |

Ưu tiên ngay: chạy `scripts/start.ps1` và acceptance trong [runtime guide](11_LITE_RUNTIME.md); hoàn thành PostgreSQL/CI và browser trước khi push/phát hành. Không mở rộng catalog bằng cách gắn nhãn đã hỗ trợ cho connector chưa có handler.

Sau core: HR là business pack đầu tiên, không đưa entity HR vào engine. Sau beta mới thêm loop/subworkflow/parallel join với semantics tường minh.
