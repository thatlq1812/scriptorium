# Archive

Bản ghi lịch sử — **history, not current state**. Nếu nội dung ở đây mâu thuẫn với `docs/specs/`, `docs/MASTER_CONTEXT.md`, hoặc code/skill thật trong `skills/`/`registry/`, thì tài liệu current thắng, không phải archive.

## pre-spec-2026-07-26/

Toàn bộ thảo luận + báo cáo nghiên cứu thô dẫn tới quyết định pivot EduStation → Scriptorium, trước khi được chưng cất thành `docs/specs/STRATEGY_SPEC.md`:

- `note.md` — ghi chú owner về môi trường làm việc, quan điểm về skill.
- `handoff.md` — bài học trả giá từ EduStation, nguyên tắc bắt buộc cho agent làm việc trên Scriptorium (đã đưa vào `docs/MASTER_CONTEXT.md` và `README.md` root).
- `conservation.md` — transcript thảo luận gốc (dán từ nơi khác) dẫn tới quyết định kiến trúc.
- `raw_research.md` — báo cáo nghiên cứu sâu gốc, có một số con số đã tự flag là chưa xác thực (xem STRATEGY_SPEC §Nguồn để biết con số nào đã sửa).
- `full_content_and_research.md` — bản merge Phần A (tổng hợp định hướng) + Phần B (toàn văn raw_research.md), là tài liệu tham chiếu đầy đủ nhất của giai đoạn thảo luận.

Con số/giả định trong các file này có thể đã lỗi thời hoặc chưa xác thực (tự các file cũng ghi rõ "cần kiểm lại" ở một số chỗ) — dùng `docs/specs/STRATEGY_SPEC.md` làm nguồn xác thực hiện tại, không trích trực tiếp từ đây.

## important-2026-07-26/

- `important.md` — chỉ thị owner về backlog mở rộng skill (4 repo nguồn ngoài, phản hồi về bài blog "Top 10" có số liệu không xác thực được, ảnh sơ đồ 42-skill tham khảo). Đã chưng cất vào `docs/ROADMAP.md`.
- `skill-org-chart-reference.jpg` — ảnh sơ đồ tổ chức skill của một sản phẩm thương mại khác, owner gửi làm cảm hứng cấu trúc mở rộng domain (không copy nội dung, xem `docs/ROADMAP.md`).

## upgrade-plan-2026-07-29/

- `UPGRADE_PLAN_20260729.md` — checklist thực thi 7 item (Personal Profile, Project Workspace, Role Capability Layer, Light Design cluster, `skill-creator` Document Distillation Mode, `skill-exporter` Knowledge Deployment Engine, Non-Tech User Guide) đưa registry từ 39 lên 62 skill. Cả 7 item đã hoàn thành (xem `docs/STATUS.md` dòng 2026-07-29 và `docs/specs/STRATEGY_SPEC.md` v1.15.0) — archive ngày 2026-08-01 vì không còn là active plan. Working rule "scout trước khi tạo skill type mới" trong file này đã được tách ra thành quy tắc thường trực trong `CLAUDE.md`, không đọc-mất khi archive.
- `request.md` — bản thảo luận chiến lược cũ giữa owner và một agent khác (dẫn tới `UPGRADE_PLAN_20260729.md`). File này gitignore từ commit `4ca42d2` (owner quyết định không track root `request.md`) — giữ nguyên untracked sau khi di chuyển, không tự ý track lại. **Lưu ý sai lệch đã sửa**: `docs/STATUS.md` dòng 2026-07-27(cont'd 2) từng khẳng định một mục "Dev Agent Response" đã được append vào file này — kiểm tra trực tiếp (2026-08-01) không thấy mục đó tồn tại trong file, khẳng định đó sai với thực tế.
