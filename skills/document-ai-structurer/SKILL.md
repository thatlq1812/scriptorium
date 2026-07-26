---
name: document-ai-structurer
description: Chuyển một tài liệu nguồn bất kỳ (PDF, DOCX, PPTX, XLSX, HTML, ảnh/scan) thành một cấu trúc thư mục tối ưu cho AI đọc — full.md (toàn văn), sections/*.md (tách theo heading), index.json (mục lục/manifest). Dùng khi cần nạp một tài liệu dài/không có cấu trúc sẵn (kể cả bản scan) vào ngữ cảnh của agent mà không phải đọc nguyên khối, hoặc cần tài liệu ở dạng agent khác dùng lại được. KHÔNG dùng để trình bày tài liệu cho người đọc trực tiếp (output tối ưu cho máy, không phải để in/xem).
license: MIT
compatibility: Cần Python 3.11+ và gói `docling` (cài qua `requirements.txt` đi kèm). Verify chạy sạch: Claude Code (2026-07-26, smoke test PDF thật, 37 sections). Chưa verify: OpenAI Codex CLI, Kimi Code CLI, Antigravity CLI.
metadata:
  domain: general
  task_type: document-conversion
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-26): ý tưởng chuyển mọi loại tài liệu thành cấu trúc tối ưu AI (thư mục + JSON mục lục) dùng Python; grounded bằng research về Docling/MinerU/unstructured.io/llms.txt convention và chunking best practice"
  engine: "docling==2.115.0"
  version: 0.1.0
---

# document-ai-structurer

Chuyển đổi một tài liệu nguồn (PDF kể cả bản scan, DOCX, PPTX, XLSX, HTML, ảnh) thành cấu trúc thư mục tối ưu cho agent đọc lại — không có chuẩn ngành sẵn cho việc này (đã research, xem `docs/specs/STRATEGY_SPEC.md` liên quan), nên đây là thiết kế riêng của Scriptorium, mượn 2 ý đã validate: JSON phân cấp kiểu Docling + nguyên tắc curated-index kiểu `llms.txt`.

## Khi nào dùng

Dùng khi: tài liệu dài, không có cấu trúc sẵn cho AI (PDF gốc, bản scan, DOCX...), và agent cần đọc lại nhiều lần hoặc chỉ cần một phần (không muốn nạp nguyên file mỗi lần). Đặc biệt hữu ích cho tài liệu luật, giáo trình, báo cáo nghiên cứu, sách — bất kỳ domain nào có tài liệu nguồn dài.

Không dùng khi: tài liệu đã là markdown/text sạch và ngắn (không cần convert); hoặc mục đích là trình bày cho người đọc (output này không có styling, không dành để in).

## Bootstrap môi trường (bắt buộc, chạy 1 lần mỗi máy)

**Không dùng `.venv` đã commit sẵn — không có, vì venv là binary gắn OS/kiến trúc, không portable.** Dùng skill `python-env-bootstrap` — venv DÙNG CHUNG ở root repo, không riêng cho skill này (không giả định máy đã có Python):

```bash
# Từ root repo:
bash skills/python-env-bootstrap/scripts/bootstrap.sh skills/document-ai-structurer/requirements.txt 3.12
# Windows: .\skills\python-env-bootstrap\scripts\bootstrap.ps1 -Requirements skills\document-ai-structurer\requirements.txt -PyVersion 3.12
```

Lần chạy đầu tiên, Docling tải model layout-detection + OCR (RapidOCR) từ HuggingFace/ModelScope về `~/.cache` hoặc local site-packages — cần mạng, vài chục MB, chỉ tải một lần.

## Chạy

```bash
# Từ root repo, venv chung:
.venv/bin/python skills/document-ai-structurer/scripts/structure_doc.py <input_file> <output_dir>
# Windows: .venv\Scripts\python.exe skills\document-ai-structurer\scripts\structure_doc.py <input_file> <output_dir>
```

## Output

```
<output_dir>/
  index.json          # manifest: source_file, title, engine, sections[], images[]
  full.md              # toàn văn markdown (đọc khi cần mạch đầy đủ)
  full_artifacts/       # ảnh trích xuất từ tài liệu (do Docling tự sinh khi có ảnh)
  sections/
    00-<slug>.md
    01-<slug>.md
    ...                # mỗi file là một section, tách theo heading level-2 (##)
```

`index.json.sections[].file` trỏ tới từng file trong `sections/` — agent tiêu thụ nên đọc `index.json` trước để quyết định đọc section nào, thay vì luôn nạp `full.md`.

## Giới hạn đã biết (v0.1.0, chưa qua quality-eval chính thức)

- Section chỉ tách theo heading level-2 (`##`). Tài liệu không có heading (hoặc chỉ có heading level-1/3+) sẽ ra 1 section duy nhất hoặc phân đoạn không như kỳ vọng — kiểm tra `index.json.sections` sau khi chạy, đừng giả định luôn tách đẹp.
- Ảnh được Docling trích ra `full_artifacts/` và tham chiếu trong `full.md`; script hiện chưa tách riêng ảnh theo section hay sinh caption/OCR-text riêng cho từng ảnh trong `index.json.images` (chỉ ghi `id` + `ref` nội bộ Docling) — cần cải tiến nếu tài liệu nguồn nặng về hình ảnh/biểu đồ.
- Chỉ smoke-test trên 1 PDF học thuật tiếng Anh (`D:/elix/researches/papers/_pdf_export/a1_3_vn_misconceptions.pdf`, 37 sections, 0 ảnh). Chưa test DOCX/PPTX/XLSX/HTML/ảnh scan tiếng Việt, chưa qua stage 4 (quality eval ≥2 harness) hay stage 5 (security audit).
