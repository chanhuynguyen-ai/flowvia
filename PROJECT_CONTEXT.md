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
M1 foundation đã được triển khai trong source: FastAPI, SQLAlchemy/Alembic, workspace identity/session, React shell, Docker app services và CI gates. Backend tests đã pass trong môi trường chuẩn bị. M1 vẫn **In progress** cho tới khi frontend lockfile + Docker startup + CI run được xác minh.

Xem `docs/09_M1_FOUNDATION.md`.

## Next vertical slice
Sau khi đóng gate M1, triển khai M2 core không phụ thuộc HR: Manual Trigger → Data Map → If/Else → Human Approval → Record Action giả lập; lưu version/run vào PostgreSQL và chạy tiếp sau restart. Sau đó mới nối luồng HR và email thật.
