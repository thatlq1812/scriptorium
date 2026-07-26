---
name: scout-harvester
description: Tìm và đánh giá sơ bộ ứng viên bên ngoài (repo GitHub, thư viện, bài báo, skill có sẵn) cho một nhu cầu skill cụ thể của Scriptorium, trước khi bất kỳ nội dung nào chạm license-compliance-check (bước 7). Dùng khi bắt đầu một skill mới và muốn biết "đã có ai giải bài này chưa, làm thế nào" trước khi tự thiết kế từ đầu. KHÔNG tự quyết định harvest/dùng — chỉ đề xuất ứng viên kèm đánh giá sơ bộ, quyết định go/no-go pháp lý luôn thuộc license-compliance-check.
license: MIT
compatibility: Quy trình research (web search + đọc code/docs), không phụ thuộc harness. Verify chạy sạch: Claude Code (2026-07-26) — đã chạy thật 3 lần trong việc xây `document-ai-structurer` (Docling/MinerU/unstructured.io), `python-env-bootstrap` (uv), và đánh giá anthropics/skills.
metadata:
  domain: meta
  task_type: research
  risk_tier: N1
  pipeline_stage: 6
  source: self-authored
  elicited_from: "Chưng cất từ 3 lần chạy thật trong phiên 2026-07-26: research công cụ document-parsing trước khi xây document-ai-structurer, research python bootstrap tool trước khi xây python-env-bootstrap, và scout anthropics/skills theo yêu cầu owner — cả ba đều theo cùng 1 pattern chưa từng viết ra thành quy trình"
  version: 0.1.0
---

# scout-harvester

Trả lời: **thứ này đã có ai làm tốt chưa, và nếu có, có đáng học/dùng không** — trước khi `skill-creator` tự thiết kế từ đầu, và trước khi bất kỳ nội dung nào được phép chạm `license-compliance-check`.

## Khi nào chạy

Ngay sau khi xác định nhu cầu một skill mới (từ elicit hoặc từ yêu cầu owner), TRƯỚC khi viết `SKILL.md`. Bỏ qua bước này = coi như tự thiết kế từ số 0, đôi khi hợp lý (nhu cầu quá đặc thù Scriptorium, ví dụ `license-compliance-check` — không có tiền lệ ngoài để scout) nhưng phải là quyết định có ý thức, không phải mặc định.

## Quy trình (rút từ 3 case thật đã chạy)

### 1. Xác định phạm vi tìm kiếm

Ba loại nguồn khác nhau, tìm theo thứ tự ưu tiên khác nhau tùy nhu cầu:
- **Công cụ/thư viện đã đóng gói** (vd Docling, uv) — ưu tiên khi cần NĂNG LỰC kỹ thuật cụ thể (parse PDF, quản lý Python env). Tìm qua: so sánh nhiều lựa chọn cùng lúc (đừng chốt cái đầu tiên tìm thấy), ưu tiên self-host/không cần API key ngoài.
- **Skill/repo có sẵn cùng ý tưởng** (vd anthropics/skills) — ưu tiên khi cần THAM KHẢO cách trình bày/quy trình cho một loại skill đã phổ biến. Kiểm marketplace lớn trước (skills.sh, agentskills.io showcase) rồi tới GitHub topic search.
- **Bài báo/tiêu chuẩn** (vd SkillsBench, llms.txt) — ưu tiên khi cần grounding phương pháp luận, không có "code để harvest" mà có "cách nghĩ để học theo".

### 2. Đánh giá sơ bộ mỗi ứng viên (KHÔNG phải audit sâu — đó là bước sau)

Cho mỗi ứng viên, trả lời nhanh 4 câu, không cần điều tra kỹ:
- Có đang được dùng/maintain thật không (activity, adoption) hay chỉ là proof-of-concept bỏ hoang?
- Input/output/năng lực có khớp đúng nhu cầu, hay chỉ "gần giống"?
- License NHÌN QUA có vẻ gì (MIT/Apache/proprietary/không rõ) — chỉ ghi nhận, KHÔNG tự kết luận go/no-go ở bước này, đó là việc của license-compliance-check.
- Có ứng viên nào rõ ràng tốt hơn hẳn (self-host, permissive, output đúng nhu cầu) để không cần so hết mọi lựa chọn?

### 3. Bàn giao

Đầu ra là một bảng ứng viên (không phải SKILL.md, không phải quyết định harvest) chuyển tới `license-compliance-check` (bước 7) cho những ứng viên có khả năng dùng code/pattern thật, hoặc thẳng tới `skill-creator` (bước 3) kèm ghi chú "grounding từ nghiên cứu X" nếu chỉ là tài liệu tham khảo phương pháp luận (không có code để check license).

## Việc scout-harvester KHÔNG làm

- Không tự quyết định license SAFE/BLOCKED — luôn bàn giao license-compliance-check.
- Không tự viết SKILL.md — đó là skill-creator.
- Không điều tra sâu từng ứng viên (đọc hết source, test hết tính năng) — đó là việc của bước sau nếu ứng viên được chọn tiếp tục.

## Case thật đã chạy (2026-07-26)

| Nhu cầu | Ứng viên tìm được | Chọn | Bàn giao |
| --- | --- | --- | --- |
| Parse PDF/DOCX/ảnh → cấu trúc AI-optimized | Docling, MinerU, unstructured.io, marker, MarkItDown, LlamaParse, Reducto | Docling (MIT, self-host, output JSON mạnh) | license-compliance-check (đã cleared) → dùng làm dependency, không copy code |
| Bootstrap Python không cần máy có sẵn Python | `uv` (Astral) | `uv` | license-compliance-check (MIT, dùng làm external tool qua installer chính thức, không vendor code) |
| Tham khảo cấu trúc skill-creator | github.com/anthropics/skills | skill-creator (Apache-2.0) trong repo đó; docx/pdf/pptx/xlsx BLOCKED | license-compliance-check (đã chạy thật, phát hiện license hỗn hợp) |
