---
name: translator-en-vi
description: Dịch văn bản Anh-Việt và Việt-Anh, giữ văn phong tự nhiên theo giọng điệu nguồn (không ép một style cố định) — nhận diện trang trọng/thân mật/kỹ thuật từ chính văn bản rồi ánh xạ sang tiếng đích. Dùng khi cần dịch tài liệu, email, mô tả kỹ thuật, hoặc bất kỳ văn bản EN/VI nào cần bản dịch đọc tự nhiên như người bản ngữ viết, không phải dịch máy móc từng từ. KHÔNG dùng cho văn bản pháp lý cần độ chính xác thuật ngữ tuyệt đối/có giá trị pháp lý (hợp đồng, văn bản luật) mà chưa qua review của người có chuyên môn — bản dịch này chỉ để tham khảo/giao tiếp, không thay thế bản dịch công chứng.
license: MIT
compatibility: Thuần instructional, không script/dependency — dùng năng lực ngôn ngữ của chính agent tiêu thụ skill. Verify chạy sạch: Claude Code (2026-07-26).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Owner (2026-07-26): không cần glossary thuật ngữ cố định, văn phong tự nhiên linh hoạt theo ngữ cảnh nguồn thay vì ép 1 style. Nội dung kỹ thuật (đối chiếu EN-VI về thì, loại từ, đại từ, thành ngữ) tự viết dựa trên hiểu biết ngôn ngữ học đối chiếu công khai."
  version: 0.1.0
---

# translator-en-vi

Dịch EN↔VI đọc tự nhiên như người bản ngữ viết, không phải dịch từng từ. Phạm vi ban đầu chỉ EN-VI/VI-EN (mở rộng ngôn ngữ khác sau nếu cần — chưa có nhu cầu cụ thể).

## Quy trình

1. **Đọc văn bản gốc, nhận diện văn phong** — trang trọng/thân mật/kỹ thuật (xem `references/register-detection.md` để có tín hiệu cụ thể cần tìm). Không mặc định một văn phong cố định cho mọi bản dịch.
2. **Dịch theo nghĩa và chức năng giao tiếp, không theo từng từ** — đặc biệt cảnh giác các điểm khác biệt cấu trúc EN↔VI liệt kê ở `references/common-pitfalls-en-vi.md` (thì động từ, loại từ, đại từ nhân xưng, thành ngữ, từ vay mượn kỹ thuật).
3. **Tự kiểm bắt buộc**: đọc lại bản dịch độc lập, không nhìn song song bản gốc — nếu phải quay lại đọc bản gốc mới hiểu bản dịch, chưa đạt, sửa lại.
4. **Rủi ro cao (risk_tier N2)**: nếu văn bản có giá trị pháp lý/hợp đồng, luôn nói rõ với người dùng rằng bản dịch này chỉ để tham khảo, không thay thế bản dịch công chứng/có chuyên môn pháp lý xác nhận.

## File đi kèm

- `references/register-detection.md` — tín hiệu nhận diện văn phong nguồn + cách ánh xạ sang tiếng đích.
- `references/common-pitfalls-en-vi.md` — 5 loại lỗi thường gặp cụ thể cho cặp EN↔VI, kèm cách xử lý.

## Việc skill này KHÔNG làm

- Không tự tạo/dùng glossary thuật ngữ cố định (owner xác nhận không cần) — quyết định theo ngữ cảnh mỗi lần.
- Không thay thế dịch thuật công chứng cho văn bản pháp lý.
- Không mở rộng sang ngôn ngữ thứ 3 ở v0.1.0 — thêm khi có nhu cầu cụ thể, không xây trước.
