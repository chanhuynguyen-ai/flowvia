# Product Specification

## 1. Product vision
Một nền tảng để cá nhân, freelancer, nhóm và doanh nghiệp tạo AI agent và lắp ghép workflow từ module, lấy cảm hứng từ trải nghiệm dạng node của n8n. HR là gói khởi đầu, không phải mô hình cố định của lõi.

## 2. Objectives
### Primary
- Builder tự tạo/chỉnh/chạy workflow cơ bản ngay beta.
- HR xử lý toàn hành trình từ hồ sơ đến lịch phỏng vấn có kiểm soát.
### Secondary
- Tái sử dụng module giữa phòng ban; đo độ tin cậy và thời gian thao tác.

## 3. Personas
### Cá nhân và freelancer
- Goal: tự tạo agent phục vụ công việc, không cần tổ chức/doanh nghiệp.
- Pain point: cấu hình kỹ thuật phức tạp và thao tác thủ công lặp lại.
- Main actions: mở workspace cá nhân, chọn mẫu hoặc canvas trống, kết nối tài khoản, chạy thử và xem kết quả.
### Nhóm nhỏ
- Goal: dùng chung quy trình và phân công quyết định.
- Main actions: tạo workspace nhóm, mời thành viên qua thao tác được cho phép, chia sẻ workflow theo quyền.

### HR Reviewer
- Goal: tìm hồ sơ phù hợp và xử lý nhanh.
- Pain point: hồ sơ phân tán, đánh giá thiếu nhất quán.
- Main actions: duyệt tiêu chí, xem bằng chứng, duyệt thư, quản lý lịch.
### Builder
- Goal: đổi quy trình không sửa mã toàn hệ thống.
- Pain point: tích hợp rời rạc và khó biết lỗi ở đâu.
- Main actions: kéo thả, mapping, test từng node, publish, xem run.
### Admin/Operator
- Goal: kiểm soát tài khoản, quyền và vận hành.
- Pain point: token hết hạn, run lỗi, không rõ ai đã gửi gì.
- Main actions: cấp quyền, kết nối, retry/đối soát và audit.

## 4. Information architecture
Workspace → Tổng quan; Workflow → Danh sách/Editor/Versions/Runs; Hộp thư; HR → Vị trí/Ứng viên/Đơn ứng tuyển; Phê duyệt; Lịch; Kết nối; Module; Cài đặt/Audit.

## 5. Feature specification
### 5.1 Workflow editor
- User value: tự nối và chạy quy trình.
- Inputs: node manifest, config, typed mappings, edges.
- Rules: beta DAG, một trigger/run; từ chối chu trình, node cô lập và input bắt buộc chưa map. Không eval biểu thức tùy ý.
- Outputs: draft, immutable published version, validation errors theo node.
- Failure cases: quyền kết nối thiếu, schema lệch, phiên bản node không tồn tại; chặn publish.
### 5.2 Run inspector
Hiển thị trạng thái, input/output đã che dữ liệu nhạy cảm theo quyền, attempts, thời gian, lỗi và quyết định. Dry-run dùng dữ liệu giả, chặn tác dụng phụ thật. Chạy node riêng chỉ với input mẫu hợp lệ.
### 5.3 Intake và kiểm tra trùng
Nhận Gmail được cấp quyền, form/webhook xác minh hoặc upload. Chuẩn hóa source/event ID, contact, vị trí và tệp. Phân biệt sự kiện trùng, tệp trùng, cùng người và cùng đơn. Email/số điện thoại trùng chỉ gợi ý liên kết nếu có mâu thuẫn; không tự hợp nhất chỉ bằng tên.
### 5.4 Tiêu chí và AI
Text/PDF/Excel → criteria draft → HR duyệt → version. Tách điều kiện bắt buộc và điểm có trọng số. AI trích xuất, dẫn chứng đoạn/trang, trả unknown khi thiếu thông tin. Lỗi model/parse chuyển cần kiểm tra, không tự loại. Xếp hạng trong cùng vị trí và phiên bản tiêu chí; không dùng đặc điểm không liên quan công việc.
### 5.5 Phê duyệt và email
Có chế độ manual/automatic theo node và policy. Manual lưu snapshot người nhận, nội dung, form URL; người có quyền duyệt có/không. Sửa nội dung sau duyệt cần duyệt lại. Automatic chỉ chạy khi policy, credential scope và dữ liệu hợp lệ. Beta không tự từ chối ứng viên. Email kèm link form, không phụ thuộc form nhúng trong Gmail.
### 5.6 Hội thoại và form
Hỏi vị trí ứng tuyển/thông tin thiếu theo mẫu; log hội thoại; người dùng có thể yêu cầu HR xử lý. Chống vòng hỏi vô hạn: tối đa 3 lượt tự động mỗi phiên rồi chuyển HR. Nội dung tuyển dụng chỉ dựa dữ liệu vị trí đã công bố. Token form ngẫu nhiên, hết hạn, giới hạn hồ sơ và loại thao tác.
### 5.7 Lịch phỏng vấn
HR mở slot gồm giờ UTC, timezone hiển thị, người phỏng vấn, sức chứa. Ứng viên chọn slot còn trống; transaction giữ chỗ; gửi xác nhận riêng từng người. Lịch ngoài và free/busy tự động là giai đoạn sau; beta không giả định đã tích hợp Calendar.
### 5.8 Dashboard
Đếm tin nhắn inbound duy nhất, ứng viên mới, đơn mới, CV duy nhất, đơn phù hợp, pending approval, thư lỗi và lịch xác nhận. Ngày theo timezone workspace; không đồng nhất tin nhắn với ứng viên. Chỉ đếm hồ sơ phù hợp theo đánh giá hiện hành.

## 6. Business rules
- Workspace cá nhân có một Owner và không yêu cầu công ty/phòng ban. Team workspace hỗ trợ thành viên/roles. tenant_id biểu diễn workspace; không thay đổi cơ chế cách ly dữ liệu.
- HR là template/pack tùy chọn, không là màn hình bắt buộc khi onboarding.
- Agent là một hay nhiều node AI có phạm vi công cụ và giới hạn; không tự có quyền hành động ngoài workflow.

- Tenant ID lấy từ phiên xác thực hoặc endpoint tích hợp đã xác minh, không tin trường do client tự gửi.
- Một candidate có nhiều application cho các job; re-application có attempt riêng.
- AI không cấp quyền, xóa hồ sơ hay tự ghi kết luận tuyển dụng cuối cùng.
- HR phê duyệt có thẩm quyền; từ chối gửi thư không tự chuyển thành loại ứng viên.
- Cấu hình AI/rules/version được lưu để truy vết, không sửa run cũ.
- Tích hợp chưa có API/quyền hợp lệ phải ghi unavailable, không hiển thị connected giả.

## 7. MVP user stories
- Builder nối Trigger → Filter → Approval → Action và chạy không sửa source.
- HR xem lý do và dẫn chứng cho từng tiêu chí trước khi quyết định.
- Operator resume run sau restart mà không gửi thư trùng.
- Admin giới hạn Builder chỉ được dùng kết nối trong phạm vi được cấp.
- Ứng viên chọn lịch mà không nhìn thấy dữ liệu người khác.

## 8. MVP acceptance criteria
- [ ] Cá nhân tạo workspace và workflow cơ bản không cần thông tin doanh nghiệp hoặc bật HR pack.
- [ ] Người dùng có thể bắt đầu từ mẫu hoặc canvas trống; HR chỉ xuất hiện khi dùng gói này.

- [ ] Tạo, save, reload, validate, publish workflow từ canvas.
- [ ] Runtime chạy đúng nhánh và ghim version; core không phụ thuộc HR.
- [ ] Manual approval tồn tại qua restart và chỉ áp dụng một lần.
- [ ] AI output sai schema không ghi kết quả hợp lệ.
- [ ] Sự kiện trùng không tạo thêm run/hành động ngoài ý muốn.
- [ ] Dữ liệu tenant A không đọc/sửa được từ tenant B, cả file/worker.
- [ ] Tạo criteria từ tài liệu cần HR xác nhận trước áp dụng.
- [ ] Gửi thư có preview, quyền và audit; kết quả không rõ được đối soát.
- [ ] Hai người chọn slot cuối đồng thời chỉ một người thành công.
- [ ] Dashboard đối chiếu được với danh sách nguồn.

## 9. Success metrics
Thời gian HR thao tác/đơn; tỷ lệ run thành công không can thiệp; tỷ lệ AI cần sửa qua tập đánh giá; tỷ lệ duplicate bị chặn; thời gian chờ duyệt. Thu baseline trước beta, chưa tuyên bố mức cải thiện.

## 10. Out of scope
App desktop native; marketplace; arbitrary code trên web; autonomous rejection; mọi connector ngay lập tức; RAG/vector DB mặc định; DAG song song/join/loop nâng cao trong beta.

## 11. Product roadmap
V1: lõi low-code + HR beta gồm AI có giới hạn. V1.1: độ tin cậy và connector được xác minh. Pro: composition/subworkflow, điều phối nâng cao, phân quyền nhiều cấp, quota và môi trường. V2: thêm business pack toàn doanh nghiệp. Quyền tạo workflow cơ bản không bị khóa ở Pro.
