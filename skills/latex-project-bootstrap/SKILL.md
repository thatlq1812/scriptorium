---
name: latex-project-bootstrap
description: Dựng khung dự án LaTeX (book/report) đúng chuẩn ngay từ đầu — XeLaTeX + fontspec/polyglossia cho tiếng Việt (không dùng pdfLaTeX + babel, dễ lỗi dấu), biblatex + biber cho bibliography, kèm build script đúng thứ tự 4-pass. Dùng khi cần bắt đầu một tài liệu LaTeX mới (sách, báo cáo nghiên cứu, luận văn) có tiếng Việt. KHÔNG dùng để tạo nội dung/chương sách thật (đó là công việc soạn thảo riêng) — skill này chỉ dựng khung kỹ thuật đúng, tránh 2 lỗi phổ biến nhất khi bắt đầu dự án LaTeX tiếng Việt từ đầu.
license: MIT
compatibility: Cần XeLaTeX (`xelatex`) + `biber` cài sẵn (MiKTeX/TeX Live). Script scaffold là Python 3 stdlib thuần, không cần venv. Verify chạy sạch: Claude Code, Windows (2026-07-26, build thật 4-pass, PDF 5 trang, tiếng Việt có dấu render đúng qua MiKTeX 25.12).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded từ dự án LaTeX thật của owner (D:/elix/researches/textbooks — chương trình sách giáo khoa dùng thật trong sản xuất): engine XeLaTeX + polyglossia/fontspec, build sequence xelatex->biber->xelatex->xelatex, quan sát trực tiếp từ textbooks/templates/core/elix-textbook.cls và docs/methodology/idea_to_book_series.md Phase 6. Tự viết scaffold generic, không copy nguyên file .cls 476 dòng đặc thù chương trình K-12 của owner."
  version: 0.1.0
---

# latex-project-bootstrap

Dựng khung dự án LaTeX đúng ngay từ lần đầu — tránh 2 lỗi phổ biến nhất khi ai đó tự bắt đầu: dùng sai engine cho tiếng Việt, và quên thứ tự build 4-pass khi có bibliography.

## Bài học nguồn (từ dự án LaTeX thật)

Đọc `references/vietnamese-latex-setup.md` trước khi viết bất kỳ file `.tex` nào — bài học rút từ một chương trình LaTeX sản xuất thật (không phải lý thuyết): pdfLaTeX + babel `vietnamese` dễ lỗi dấu thanh khi phối với font hiện đại; XeLaTeX + `fontspec`/`polyglossia` xử lý Unicode trực tiếp, ổn định hơn nhiều.

## Dựng khung dự án

```bash
python scripts/init_project.py <output_dir> --title "Tên tài liệu" --font "Noto Serif"
```

Sinh ra: `main.tex` (preamble XeLaTeX đúng chuẩn + biblatex/biber), `chapters/01_intro.tex`, `bibliography.bib` mẫu, `build.sh`/`build.ps1`.

## Build

```bash
# Unix:
bash build.sh
# Windows PowerShell:
.\build.ps1
```

Thứ tự bắt buộc (xem `references/vietnamese-latex-setup.md` để biết vì sao từng bước cần thiết): `xelatex → biber → xelatex → xelatex`. Bỏ qua bất kỳ pass nào có thể ra PDF thiếu citation hoặc mục lục/số trang sai.

## Việc skill này KHÔNG làm

- Không tạo nội dung chương sách thật — chỉ dựng khung kỹ thuật (preamble, build script).
- Không cài đặt TeX distribution (MiKTeX/TeX Live) — giả định đã có sẵn trên máy, kiểm bằng `xelatex --version` trước khi dùng skill.
- Không dùng custom class phức tạp (kiểu `elix-textbook.cls` của dự án nguồn, có macro riêng cho SGK) — dùng `book` class chuẩn + preamble tối giản, để skill portable cho mọi loại tài liệu, không chỉ sách giáo khoa.

## File đi kèm

- `scripts/init_project.py` — scaffold, stdlib thuần.
- `references/vietnamese-latex-setup.md` — bài học kỹ thuật + preamble mẫu + lỗi thường gặp.

## Giới hạn đã biết (v0.1.0)

- Chỉ scaffold `book` class đơn giản (1 chương mẫu) — chưa hỗ trợ multi-volume, TikZ figures, hay custom environment (những thứ dự án nguồn có nhưng đặc thù riêng, không tổng quát hóa được ngay).
- Chưa test với font khác ngoài "Noto Serif"/"Times New Roman" — nếu font không có trên máy build, `xelatex` báo lỗi rõ ràng ("Font not found"), không silent fail.
