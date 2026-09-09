# Application Flow

## 1. End-to-end overview
Builder → canvas → validate/publish → trigger → persistent run → typed nodes → human/action → audit. HR chỉ cung cấp các node chuyên biệt.

## 2. Authentication flow
Login → kiểm tra user active/membership → tạo session → chọn workspace được phép → kiểm tra quyền mỗi request. Logout/thu hồi session làm mất quyền; link ứng viên là scoped token riêng, không phải session nội bộ. Refresh/expiry phải triển khai và test khi xây auth.

## 3. Primary happy path
1. Admin cấu hình workspace, timezone và credential; Builder chỉ chọn credential reference có quyền.
2. HR tạo job và nhập tiêu chí; tài liệu nhập được trích thành draft, HR xác nhận version.
3. Builder nối Trigger → normalize → duplicate check → HR upsert → document extract → AI evaluation → Router → approval → email; validate và publish.
4. Nhận hồ sơ, xác minh sự kiện, ghi event/outbox; worker tạo run theo version.
5. Trích xuất và đánh giá với bằng chứng; thiếu dữ liệu đi nhánh hỏi thêm; AI lỗi đến hàng chờ.
6. Hồ sơ phù hợp: manual chờ HR duyệt snapshot; automatic gửi khi policy cho phép. Không tự loại hồ sơ chưa phù hợp.
7. Email chứa link form/lịch theo mục đích; ứng viên gửi thông tin bổ sung qua workflow mới liên kết application hoặc chọn slot.
8. Lưu booking trước khi gửi xác nhận; dashboard và timeline cập nhật từ trạng thái chuẩn.

## 4. State transitions
| Current state | Action | Next state | Actor | Guard |
|---|---|---|---|---|
| draft | publish | published version | Builder | schema + permissions + revision valid |
| queued | claim | running | Worker | lease và version tồn tại |
| running | request approval | waiting_human | Engine | snapshot và approver scope hợp lệ |
| waiting_human | approve/reject | running | Reviewer | pending, cùng tenant, quyền, atomic decision |
| running | all active steps done | succeeded | Engine | không còn bước chờ |
| running | exhausted retries | failed | Engine | attempt limit |
| queued/running/waiting_human | cancel | cancelled | Operator | quyền cancel; chặn action chưa dispatch |
| approval pending | expire | expired | Scheduler | deadline; không auto-approve |
| message queued | send acknowledged | sent | Adapter | receipt/provider ID |
| message dispatching | ambiguous timeout | delivery_unknown | Adapter | chưa xác định provider đã nhận |
| slot available | reserve | confirmed booking | Candidate | token hợp lệ, capacity transaction |

Application: received → needs_information/under_review → shortlisted → invited → interview_scheduled → closed. Chỉ HR có quyền chuyển quyết định cuối; không ánh xạ reject approval thành rejected candidate tự động.

## 5. Protected action flow
Authenticate → tenant/resource authorization → validate → transaction + outbox → commit → worker dispatch → receipt/audit. Preview không tự cấp quyền gửi; live run kiểm tra lại.

## 6. Failure and exception flows
- Invalid graph/input: 422 chi tiết node/field, không publish/action.
- Permission denied: 403 hoặc 404 để không lộ resource; audit thích hợp.
- Edit/approval conflict: 409, refresh; không ghi đè quyết định đã có.
- Duplicate webhook: trả receipt cũ sau kiểm tra authenticity, không tạo run trùng.
- Connector hết hạn: action blocked, yêu cầu quản trị reconnect.
- File hỏng/OCR không đọc được/model invalid: needs_review; không chấm 0 tự động.
- Missing job: hỏi ứng viên hoặc HR chọn, chưa chấm điểm.
- Replayed approval/link: không tạo thêm action; token hết hạn trả trang hướng dẫn.
- Email unknown: đối soát provider/manual, không retry mù.
- Slot hết chỗ: trả conflict và danh sách slot còn lại.
- Restart: worker nhận bước có lease hợp lệ, run chờ giữ nguyên DB.

## 7. Complete demo scenario
Dùng 5 hồ sơ giả: phù hợp, thiếu thông tin, chưa đáp ứng, gửi lại cùng sự kiện và tệp không đọc được. Kiểm tra chỉ có 4 sự kiện mới nếu lần gửi lại giữ event ID; số candidate/application tùy identity, không suy từ số messages. HR duyệt một thư, từ chối một yêu cầu gửi. Restart khi chờ duyệt, sau đó duyệt thành công đúng một lần. Hai ứng viên cạnh tranh slot cuối; chỉ một booking confirmed. Thử tenant khác không đọc được hồ sơ/run/file. Chỉnh canvas thêm approval vào workflow xử lý yêu cầu nội bộ để chứng minh core dùng ngoài HR.
