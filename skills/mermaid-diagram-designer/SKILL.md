---
name: mermaid-diagram-designer
description: Thiết kế diagram-as-code bằng cú pháp Mermaid (flowchart, sequence, class, state, ER, gantt, pie, journey, mindmap, timeline) từ mô tả một hệ thống/quy trình/quan hệ dữ liệu. Dùng khi cần trực quan hóa quy trình, tương tác giữa nhiều thành phần, mô hình dữ liệu, hoặc timeline dự án dưới dạng text nhúng được vào markdown/HTML. KHÔNG dùng cho biểu đồ dữ liệu định lượng phức tạp nhiều series/trục (đó là việc của matplotlib/Recharts/D3) — Mermaid mạnh về cấu trúc/quan hệ, không phải data visualization.
license: MIT
compatibility: Sinh ra text thuần (không cần render để giao cho người dùng — hầu hết harness/markdown viewer hiện đại tự render code fence ```mermaid```). Script lint đi kèm là Python 3 stdlib thuần, không cần venv. Verify chạy sạch: Claude Code, Windows (2026-07-26, lint script test cả case hợp lệ và case lỗi).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-26, docs/ROADMAP.md): scout mermaid-js/mermaid (MIT, 89,421 sao, verify trực tiếp qua gh api) làm nguồn cú pháp. Cheatsheet + quy tắc chọn loại diagram tự viết lại bằng lời riêng (không copy nguyên văn tài liệu gốc), dựa trên hiểu biết cú pháp Mermaid công khai."
  version: 0.1.0
---

# mermaid-diagram-designer

Chuyển một mô tả hệ thống/quy trình/quan hệ thành diagram-as-code Mermaid hợp lệ, đúng loại diagram cho đúng loại thông tin.

## Quy trình

1. **Xác định loại diagram** — đọc `references/choosing-diagram-type.md`, áp quy tắc quyết định nhanh (có trục thời gian thật? nhiều actor tương tác? có trạng thái/sự kiện? có quan hệ dữ liệu tĩnh?). Không mặc định `flowchart` cho mọi thứ chỉ vì nó linh hoạt nhất — chọn sai loại diagram làm người đọc hiểu sai bản chất hệ thống.
2. **Viết diagram** — tham khảo cú pháp đúng loại đã chọn ở `references/syntax-cheatsheet.md`.
3. **Lint trước khi giao** — chạy `scripts/lint_mermaid.py` trên diagram vừa viết:
   ```bash
   python scripts/lint_mermaid.py <file.mmd>
   # hoặc: echo "..." | python scripts/lint_mermaid.py -
   ```
   Đây là lint cấu trúc thô (từ khóa loại diagram hợp lệ, ngoặc cân đối, quote cân đối) — KHÔNG phải render thật, không bắt được mọi lỗi cú pháp (vd sai tên arrow type). Nếu có điều kiện render thật (Mermaid Live Editor, VS Code extension, hoặc harness hỗ trợ render mermaid trực tiếp trong markdown), luôn ưu tiên verify bằng render thật.
4. **Giao diagram** trong code fence ```` ```mermaid ```` nếu output là markdown, hoặc `<pre class="mermaid">...</pre>` nếu output là HTML (Artifact convention).

## Việc skill này KHÔNG làm

- Không tự render ảnh (PNG/SVG) — cần Node + `@mermaid-js/mermaid-cli` (nặng, cần Puppeteer/Chromium), chưa xây trong v0.1.0. Giao diagram dạng text, để harness/viewer đích render.
- Không dùng cho chart dữ liệu định lượng nhiều chiều — xem skill `dataviz` (nếu có) hoặc công cụ chart chuyên dụng.

## File đi kèm

- `references/syntax-cheatsheet.md` — cú pháp mẫu cho 10 loại diagram.
- `references/choosing-diagram-type.md` — bảng quyết định chọn loại diagram theo tình huống.
- `scripts/lint_mermaid.py` — lint cấu trúc thô, stdlib thuần.

## Giới hạn đã biết (v0.1.0)

- Lint chỉ bắt lỗi cấu trúc bề mặt (từ khóa, ngoặc, quote) — không phải parser Mermaid thật, có thể pass sai hoặc fail nhầm với cú pháp phức tạp (styling, subgraph lồng nhau, click events).
- Chưa test trên diagram thật lớn (>50 node) — chỉ verify case nhỏ.
