---
name: office-doc-creator
description: Tạo file Word (.docx), PowerPoint (.pptx), Excel (.xlsx) thật từ một JSON content spec đơn giản, dùng thư viện MIT (python-docx, python-pptx, openpyxl) — không phải viết XML thủ công, không phụ thuộc Anthropic hay bất kỳ dịch vụ AI nào. Dùng khi cần xuất kết quả agent (báo cáo, hợp đồng, công văn, bảng dữ liệu, slide) thành file Office thật có thể mở bằng Word/Excel/PowerPoint. KHÔNG dùng để ĐỌC/phân tích file Office có sẵn (đó là `document-ai-structurer`) — skill này chỉ TẠO MỚI.
license: MIT
compatibility: Cần Python 3.11+ + `python-docx`/`python-pptx`/`openpyxl` (bootstrap qua `python-env-bootstrap`). Verify chạy sạch: Claude Code, Windows qua PowerShell (2026-07-26, smoke test cả 3 định dạng, xác nhận đọc lại nội dung tiếng Việt có dấu đúng).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-26): mở rộng scout ra ngoài Anthropic, dựng 'office skills' từ nguồn khác vì docx/pdf/pptx/xlsx của Anthropic bị khóa license. Scout tìm được python-docx/python-pptx/openpyxl (MIT, xác minh trực tiếp qua pip show + PyPI JSON API), tự viết implementation từ đầu."
  version: 0.1.0
---

# office-doc-creator

Tạo file Office thật (không phải giả lập) từ nội dung agent đã chuẩn bị sẵn dưới dạng JSON. Ba script độc lập, mỗi định dạng một file — không dùng chung một "mega script".

## Vì sao tự viết thay vì dùng skill docx/pptx/xlsx của Anthropic

Đã scout (`scout-harvester`) và kiểm license (`license-compliance-check`) — skill tương ứng của Anthropic có điều khoản hợp đồng cấm tuyệt đối extract/copy/derive/distribute, BLOCKED hoàn toàn. `python-docx`/`python-pptx`/`openpyxl` là thư viện MIT độc lập, không liên quan tới Anthropic, verify license trực tiếp (`pip show`, PyPI JSON API) ngày 2026-07-26 — an toàn tự viết implementation riêng.

## Bootstrap môi trường

Venv DÙNG CHUNG ở root repo (không riêng cho skill này — xem `skills/python-env-bootstrap/SKILL.md`):

```bash
# Khuyến nghị: qua python-env-bootstrap (PowerShell trên Windows, KHÔNG qua Git Bash):
.\skills\python-env-bootstrap\scripts\bootstrap.ps1 -Requirements skills\office-doc-creator\requirements.txt -PyVersion 3.12
```

## Tạo file Word (.docx)

```bash
# Từ root repo, venv chung:
.venv\Scripts\python.exe skills\office-doc-creator\scripts\create_docx.py <content.json> <output.docx>
```

`content.json`:
```json
{
  "title": "Tiêu đề tài liệu",
  "blocks": [
    {"type": "heading", "level": 1, "text": "Phần 1"},
    {"type": "paragraph", "text": "Nội dung đoạn văn."},
    {"type": "table", "headers": ["Cột A", "Cột B"], "rows": [["1", "2"]]}
  ]
}
```

## Tạo file Excel (.xlsx)

```bash
.venv\Scripts\python.exe skills\office-doc-creator\scripts\create_xlsx.py <content.json> <output.xlsx>
```

`content.json`: `{ "sheets": [{ "name": "Sheet1", "headers": [...], "rows": [[...], ...] }] }`

## Tạo file PowerPoint (.pptx)

```bash
.venv\Scripts\python.exe skills\office-doc-creator\scripts\create_pptx.py <content.json> <output.pptx>
```

`content.json`: `{ "slides": [{ "title": "...", "bullets": ["...", "..."] }] }` — dùng layout "Title and Content" mặc định của PowerPoint, không custom theme.

## Giới hạn đã biết (v0.1.0)

- Không hỗ trợ style/theme phức tạp, ảnh chèn vào, hay template công ty riêng — chỉ tạo cấu trúc nội dung thô (heading/paragraph/table cho docx; sheet/row cho xlsx; title/bullet cho pptx). Nếu cần branding/template, mở rộng script hoặc dùng `python-docx`'s `Document(template_path)` trực tiếp.
- Chưa test file cực lớn (>100 trang/slide/sheet) — chỉ verify với nội dung nhỏ.
- Chưa qua stage 4 (quality eval) chính thức; security-audit đã chạy (self-audit, không finding — scripts chỉ đọc JSON local, ghi file local, không network call, không secret handling).
