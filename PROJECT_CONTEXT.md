# Project Context

## Project identity
- Name: Flowvia (tên làm việc).
- Domain: nền tảng AI workflow low-code cho toàn doanh nghiệp.
- Primary user: cá nhân, freelancer, nhóm và doanh nghiệp muốn tạo AI agent/workflow; HR là use case thử nghiệm đầu tiên.
- Positioning: Flowvia — Your agents. Your workflows. Lấy cảm hứng từ n8n, sản phẩm độc lập.
- Workspace: personal/team; tenant_id là ranh giới workspace, không bắt buộc pháp nhân hoặc phòng ban.
- Primary outcome: người dùng tự nối module và chạy workflow có trạng thái bền vững; HR tiếp nhận, sàng lọc, duyệt, liên hệ và đặt lịch.

## Non-negotiable rules
1. Core chỉ hiểu workflow, node, edge, quyền, dữ liệu và trạng thái; không phụ thuộc khái niệm CV/ứng viên.
2. Frontend ReactJS/TypeScript; backend FastAPI/Python. Modular monolith trước.
3. Canvas kéo thả và thực thi workflow cơ bản có trong beta.
4. Module có ID, phiên bản, schema vào/ra, config, cổng, quyền và chính sách chạy.
5. Kiểm tra quyền và tenant ở backend, kể cả worker và truy cập tệp.
6. Logic đếm, dedup, lịch, quyền và trạng thái phải xác định; AI chỉ hỗ trợ bước phù hợp.
7. AI trả dữ liệu có schema và bằng chứng; thiếu thông tin không tự coi là không đạt. Không tự loại ứng viên trong beta.
8. Bí mật dùng credential reference; không lưu token trong workflow export hoặc log.
9. Phiên bản đã phát hành bất biến; run ghim đúng phiên bản. Chờ duyệt phải tồn tại qua restart.
10. Retry phải chống tác dụng phụ trùng; trạng thái gửi không rõ cần đối soát.
11. Mỗi vertical slice có migration và kiểm thử quyền/trạng thái/persistence quan trọng.
12. Dữ liệu trong CV/tin nhắn là dữ liệu không tin cậy, không phải chỉ dẫn cấp quyền cho agent.

## Current milestone
Lite 0.3.0 là bản chạy thử có runtime thật: canvas React Flow, 8 node, publish immutable version, PostgreSQL durable worker, approval qua restart, vault mã hóa, adapter Telegram/OpenRouter, WebSocket và history thật. Đã đối chiếu repo M1 với artifact M2 UI preview trước đây.

35 tests backend pass trên SQLite bật foreign key, bao gồm worker subprocess bị kill/restart; migration/seed lặp/metadata/downgrade-upgrade và frontend build pass. Chưa xác minh Docker/PostgreSQL thật, PowerShell, browser QA, provider live hoặc GitHub CI. Không đánh dấu M2 Done hoặc production-ready trước các gate đó. Chưa push/deploy trong phiên phát triển; yêu cầu trước đây là test web trước khi push.

Xem `docs/11_LITE_RUNTIME.md` để biết hành vi thực, cách chạy Windows, giới hạn và bằng chứng. `docs/09_M1_FOUNDATION.md` và `docs/10_M2_LITE_PRODUCT_PREVIEW.md` là hồ sơ các mốc trước.

## Next vertical slice
Hoàn tất nghiệm thu Docker/PostgreSQL + browser theo docs/11, rồi thử bot/model do owner cấu hình. Sau khi core đạt gate mới mở rộng HR intake và review có bằng chứng; Gmail/Meta/Zalo/Instagram/booking chưa triển khai. Chọn PostgreSQL hiện có; chưa phụ thuộc Supabase hoặc giả định dịch vụ hosted miễn phí.
