# UI/UX Guide

## 1. Design direction
Hiện đại, chuyên nghiệp, rõ trạng thái, desktop-first. Giao diện nghiệp vụ và canvas chung một shell; thuật ngữ tiếng Việt, tên kỹ thuật ở chế độ nâng cao.

## 2. Visual identity
- Primary: #4F46E5; Accent: #0891B2.
- Neutral: nền #F8FAFC, surface #FFFFFF, text #0F172A, secondary #475569, border #E2E8F0.
- Success #15803D / warning #A16207 / danger #B91C1C / info #1D4ED8; luôn kèm nhãn/icon.
- Đây là token đề xuất; kiểm tra contrast với phối màu thực tế khi triển khai.

## 3. Typography
Font hệ thống hỗ trợ tiếng Việt; có thể dùng Inter nếu đóng gói phù hợp. H1 28/36; H2 22/30; H3 18/26; body 14/22; label 13/20; meta 12/18 px. Số liệu không lấn át tác vụ cần xử lý.

## 4. Spacing and geometry
Spacing 4/8/12/16/24/32; radius 8 cho control, 12 cho card; border 1 px. Bảng mật độ vừa, row 44–48 px; focus ring nhìn rõ.

## Onboarding và tên hiển thị
Thương hiệu Flowvia, tagline “Your agents. Your workflows.” Hiển thị “Không gian làm việc” thay vì mặc định “Doanh nghiệp”. Cá nhân chọn bắt đầu nhanh bằng mẫu hoặc canvas; nhóm dùng cấu hình thành viên riêng. HR là pack tùy chọn trong navigation. Mẫu agent cá nhân là định hướng cần triển khai, không hiển thị trạng thái chạy thật khi chưa có handler.

## 5. Global layout
Sidebar 232 px có workspace switcher; topbar 56 px; content padding 24 px. Canvas có node palette trái 248 px, vùng đồ thị giữa, configuration drawer phải 360 px; run inspector mở phía dưới. Toolbar: Lưu nháp, Kiểm tra, Chạy thử, Phát hành, Chạy thật; live run có nhãn rõ môi trường/tác dụng phụ.

## 6. Core screens
| Screen | Content and main action |
|---|---|
| Overview | Tin nhắn/ứng viên/đơn/CV riêng biệt; queue chờ duyệt và lỗi; drill-down cùng bộ lọc |
| Workflows | Template, trạng thái, version, lần chạy gần nhất; tạo mới |
| Editor | Kéo thả, cổng typed, mapping picker, lỗi tại node; save/test/publish |
| Runs | Timeline node, attempts, input/output theo quyền, resume/cancel hợp lệ |
| Inbox | Nguồn, hội thoại, liên kết candidate/application, chuyển HR |
| HR Jobs | JD, tiêu chí bắt buộc/trọng số, version criteria |
| Applications | Bảng/Kanban, nguồn, job, mức phù hợp, trạng thái; lọc |
| Candidate detail | CV và bằng chứng song song; nhiều đơn ứng tuyển; lịch sử |
| Approvals | Recipient/content preview, approve/reject, chọn nhiều và kiểm tra từng item |
| Calendar | Slot, capacity, người phỏng vấn, múi giờ, trạng thái |
| Connections | disconnected/connected/expired/error/unavailable, scope và lần sync |
| Module catalog | Nhóm node, ports, cấu hình, version; module chưa hỗ trợ disabled |

Node màu theo loại kèm icon, không theo phòng ban. Mapping hiển thị tên trường và kiểu, ví dụ “Email ứng viên · text”; advanced JSON là tùy chọn. Không lộ token hoặc yêu cầu người dùng hiểu database để hoàn thành nghiệp vụ.

## 7. Component states
Empty có CTA đúng quyền; loading skeleton; error có retry thích hợp và request ID; disabled có lý do; success có kết quả; confirmation hiển thị đối tượng/tác động. Autosave phải báo saving/saved/conflict, không giả đã lưu. Approval hết hạn không còn nút approve hoạt động.

## 8. Responsive behavior
Desktop ≥1280: editor đầy đủ. Tablet 768–1279: drawer overlay và palette thu gọn. Mobile: xem run/duyệt/form/lịch; editor chuyển xem và hướng dẫn mở desktop, không ép kéo thả vào màn hình nhỏ. Form ứng viên dùng tốt trên mobile.

## 9. Accessibility
Keyboard focus, nhãn form, lỗi cạnh trường và summary; không chỉ dùng màu. Có cách thêm/nối node bằng danh sách bàn phím; zoom không khóa focus. Kiểm tra contrast, tab order, screen reader nhãn nút và giảm animation. Luôn hiển thị timezone cho lịch; dùng text wrap cho tên dài tiếng Việt.
