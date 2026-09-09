# Project Overview

## 1. Project summary
Flowvia là nền tảng AI agent và workflow low-code đa đối tượng. Người dùng chọn module, nối cổng, ánh xạ dữ liệu, cấu hình và chạy quy trình. HR là business pack đầu tiên; tương lai thêm Sales, CSKH, vận hành và tài chính theo cùng hợp đồng.

## Định vị và đối tượng mở rộng
Flowvia — **Your agents. Your workflows.** Phục vụ cá nhân, freelancer, creator, nhóm nhỏ và doanh nghiệp. Cho phép bắt đầu bằng mẫu agent/workflow hoặc canvas trống. Lấy cảm hứng từ n8n ở trải nghiệm nối node, không tuyên bố là bản fork hay sản phẩm chính thức của n8n. HR vẫn là gói beta đầu tiên; quản lý email, tài liệu và yêu cầu cá nhân là hướng mở rộng. Tên thương mại chưa được xác minh.

## 2. Problem being solved
Dữ liệu đầu vào phân tán, thao tác nhập liệu lặp lại, khó biết công việc đang ở bước nào. Trong tuyển dụng, HR phải tải CV, kiểm tra trùng, đối chiếu yêu cầu, liên hệ và sắp lịch thủ công.

## 3. Value proposition
### For người thiết kế quy trình
Thay đổi trình tự và điều kiện bằng cấu hình, tái sử dụng module thay vì sửa toàn ứng dụng.
### For HR và người vận hành
Một nơi xem hồ sơ, bằng chứng đánh giá, việc chờ duyệt, thư và lịch sử xử lý.
### For quản trị doanh nghiệp
Kiểm soát quyền, kết nối, nhật ký và khả năng mở rộng sang phòng ban khác.

## 4. Core capabilities
- Canvas, node palette, cấu hình, ánh xạ, validate, test, publish, run.
- Runtime bền vững, phân nhánh, chờ duyệt, retry, nhật ký và giới hạn tài nguyên.
- Connector chuẩn hóa sự kiện đa nguồn; AI adapter đầu ra có cấu trúc.
- HR pack: vị trí, đơn ứng tuyển, CV, tiêu chí, đánh giá, thư, form, lịch và thống kê.

## 5. Main user roles
Owner/Admin; Builder; Operator; HR Reviewer; Hiring Manager; Viewer. Một người có thể nhận nhiều vai trò. Ứng viên chỉ có quyền với form/link của mình.

## 6. High-level modules
Platform: identity, connections, module registry, workflows, executions, approvals, files, notifications, scheduling, analytics, audit.
Business pack: HR; các pack khác chưa triển khai. Lõi không import HR; HR đăng ký node qua registry.

## 7. Product principles
Lõi xác định, cấu hình được, kiểm tra được, tenant isolation, audit hành động quan trọng, modular monolith. AI có ngay beta sau khi cơ chế chạy cơ bản ổn định. Không cam kết API của nguồn chưa xác minh.

## 8. MVP scope
Low-code cơ bản: kéo thả, nhánh điều kiện, ánh xạ, kiểm tra lỗi, chạy thử, lưu/publish version, xem run và chờ duyệt.
HR: Gmail/form/upload, PDF/DOCX và trạng thái cần kiểm tra với tệp không đọc được; nhập tiêu chí bằng text và tài liệu PDF/Excel thành bản nháp HR xác nhận; kiểm tra trùng; đánh giá có bằng chứng; thư theo mẫu; form bổ sung; chọn lịch từ slot HR mở; dashboard.
Tự động gửi chỉ cho action được cấp quyền và cấu hình trước; mặc định duyệt thư mời. Hội thoại beta có kịch bản giới hạn: xác nhận tiếp nhận, hỏi vị trí và dữ liệu thiếu, chuyển HR.

## 9. Non-functional goals
### Security
Tách tenant; secret mã hóa ngoài export; quyền ở backend/worker; URL tệp hết hạn; hạn chế dữ liệu log.
### Reliability
Lưu trạng thái trước/sau mỗi bước; dedup sự kiện; outbox; resume phê duyệt sau restart; phát hiện gửi không rõ kết quả.
### Performance
Mục tiêu thử nghiệm, chưa đo: API danh sách p95 dưới 500 ms trên dữ liệu demo 10.000 đơn; phản hồi nhận webhook dưới 2 giây sau ghi bền vững; AI chạy nền. Đặt benchmark môi trường cụ thể trước nghiệm thu.
### Maintainability
Node version hóa và contract tests; domain modules; khóa dependency khi bootstrap; CI có kiểm tra phù hợp mức triển khai.

## 10. Development direction
- Stage 1: runtime/canvas chung và luồng HR tối thiểu.
- Stage 2: beta HR đầy đủ, AI, phê duyệt, email và lịch.
- Stage 3: Pro: subworkflow, nhánh song song/gộp, vòng lặp giới hạn, quản trị nâng cao.
- Stage 4: connector đã được cấp quyền và business pack khác.
- Stage 5: tách dịch vụ khi có bằng chứng về nhu cầu mở rộng.

## 11. Definition of success
HR chỉnh workflow trên canvas, chạy hồ sơ giả lập, thấy dedup và đánh giá giải thích được, duyệt thư, ứng viên chọn slot. Một workflow xử lý yêu cầu nội bộ dùng lại node phê duyệt và thông báo mà không sửa core. Chạy lại sự kiện không tạo thư/lịch trùng.
