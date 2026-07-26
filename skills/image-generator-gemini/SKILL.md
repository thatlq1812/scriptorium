---
name: image-generator-gemini
description: Bộ công cụ designer dùng Gemini (google-genai SDK) qua API key RIÊNG của người dùng — tùy chọn, không phải backend AI do Scriptorium quản lý. Không chỉ tạo ảnh đơn lẻ: hỗ trợ style-anchoring (1 ảnh tham chiếu), auto-anchor batch (cả bộ asset tự đồng bộ phong cách quanh ảnh đầu tiên, không cần chuẩn bị mẫu trước), vision-analysis (đọc một ảnh có sẵn, mô tả phong cách thành text để tái dùng), và trích cover từ PDF có sẵn (không cần AI, render local). Dùng khi người dùng đã có Gemini API key và cần tạo/phân tích/trích xuất asset hình ảnh — từ 1 icon đơn tới cả bộ brand/cover đồng bộ. KHÔNG dùng nếu người dùng chưa có key riêng, và không phải lối tắt né nguyên tắc "Scriptorium không tích hợp AI backend" (xem ghi chú bên dưới).
license: MIT
compatibility: Cần Python 3.11+ + `google-genai` + `pypdfium2` (đã có sẵn qua transitive dep của `document-ai-structurer` trong venv chung — bootstrap qua `python-env-bootstrap`) + biến môi trường `GEMINI_API_KEY` của chính người dùng. Verify chạy sạch: Claude Code, Windows (2026-07-26) — verify THẬT bằng API call thật cho cả 4 khả năng: ảnh đơn lẻ, batch + skip-if-exists, style-ref anchoring, vision-analysis (mô tả phong cách đúng, chi tiết), PDF-page-extraction (render trang PDF thật, đọc được text).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded từ 3 dự án riêng của owner: D:/elix/platform/scripts/gen/ (9 script gen_*.py — pattern batch/style-chain/brand-identity/PDF-cover quan sát qua khảo sát chữ ký hàm), D:/UNI/S9_SP26/MLN131/project/scripts/ (gen-images-v2.mjs: batch+skip-if-exists; gen-slide-images.mjs: style-ref anchoring; gen_marketing_images.py generate_pack(): auto-anchor từ ảnh đầu batch nếu chưa có style_ref, pattern 'anchor'/'chained' tag). Tự viết lại toàn bộ bằng Python, tổng quát hóa, bỏ phần gắn cứng GCS/DB/style-rules đặc thù project gốc."
  version: 0.3.0
---

# image-generator-gemini

Bộ công cụ designer, không chỉ generator đơn lẻ: tạo ảnh, giữ nhất quán phong cách qua nhiều ảnh (2 cách: anchor thủ công hoặc auto-anchor), đọc/mô tả phong cách ảnh có sẵn, và trích cover từ PDF không cần AI.

## Quan trọng — không mâu thuẫn với nguyên tắc "không tích hợp AI backend"

`docs/specs/STRATEGY_SPEC.md` §2 nói Scriptorium không tích hợp AI backend nào — nguyên tắc đó nói về **Scriptorium tự nó** không đứng giữa như một service gọi LLM hộ ai bằng credential của chính Scriptorium. Skill này khác bản chất: nó là instruction cho agent gọi API **bằng key của chính người dùng đang chạy skill** (bring-your-own-key), hoàn toàn tùy chọn — giống một skill "gửi email qua SendGrid" dùng SendGrid key riêng của người dùng. Không phải Scriptorium cấp key, quản lý billing, hay bắt buộc dùng.

## Bootstrap môi trường

Venv DÙNG CHUNG ở root repo (xem `skills/python-env-bootstrap/SKILL.md`):

```bash
.\skills\python-env-bootstrap\scripts\bootstrap.ps1 -Requirements skills\image-generator-gemini\requirements.txt -PyVersion 3.12
```

## Ảnh đơn lẻ

```bash
export GEMINI_API_KEY="key-cua-ban"   # hoặc --api-key
.venv\Scripts\python.exe skills\image-generator-gemini\scripts\generate_image.py "mô tả ảnh cần tạo" output.png
```

## Style-anchoring thủ công — giữ nhất quán phong cách với 1 ảnh mẫu có sẵn

```bash
.venv\Scripts\python.exe skills\image-generator-gemini\scripts\generate_image.py "mô tả ảnh mới" output2.png --style-ref output.png
```

`--style-ref` gửi kèm ảnh tham chiếu + instruction "STRICT style reference" trước prompt chính — model match palette/lighting/line-weight của ảnh tham chiếu khi vẽ chủ thể mới.

## Batch với auto-anchor — cả bộ asset tự đồng bộ phong cách, không cần mẫu trước

```bash
.venv\Scripts\python.exe skills\image-generator-gemini\scripts\generate_image.py --batch manifest.json --out-dir assets/
```

`manifest.json` (xem `scripts/batch_manifest.example.json`):
```json
{
  "style_ref": "path/to/reference.png hoặc null",
  "images": {
    "ten-file-1.png": "prompt cho ảnh 1",
    "ten-file-2.png": "prompt cho ảnh 2"
  }
}
```

Nếu `style_ref` là **null**: **auto-anchor** — ảnh ĐẦU TIÊN sinh ra trong batch tự động trở thành style reference cho MỌI ảnh sau đó (pattern quan sát thật từ `generate_pack()` của dự án MLN131 — tag log "(anchor)" cho ảnh đầu, "(chained)" cho các ảnh sau). Không cần chuẩn bị ảnh mẫu trước khi bắt đầu — cả bộ tự đồng bộ quanh item đầu tiên. Nếu chạy lại batch dở dang, ảnh đã có (skip) cũng được dùng làm anchor, không mất tính nhất quán giữa các lần chạy.

Đặc điểm khác: **skip-if-exists** (an toàn khi batch fail giữa chừng), **rate-limit delay** giữa mỗi request (mặc định 3s, chỉnh qua `--delay`).

## Vision-analysis — đọc một ảnh có sẵn, mô tả phong cách thành text

```bash
.venv\Scripts\python.exe skills\image-generator-gemini\scripts\analyze_style.py reference.png
```

Trả về đoạn mô tả phong cách (palette, lighting, line-weight, composition — KHÔNG mô tả chủ thể) dùng làm prompt prefix cho lần generate sau, hoặc để hiểu một brand/design system có sẵn trước khi tạo ảnh mới khớp nó. Verify thật: mô tả đúng, chi tiết, đúng cấu trúc yêu cầu (đã test 2026-07-26).

## Trích cover từ PDF — KHÔNG cần AI, render local

```bash
.venv\Scripts\python.exe skills\image-generator-gemini\scripts\extract_pdf_page.py document.pdf cover.png --page 0 --scale 2.0
```

Dùng `pypdfium2` (đã có sẵn qua dep của `document-ai-structurer`) render 1 trang PDF thành PNG — không gọi API, không tốn phí, không cần `GEMINI_API_KEY`. Dùng khi cần cover/thumbnail từ tài liệu ĐÃ CÓ (khác các lệnh trên, vốn TẠO MỚI ảnh từ mô tả).

## Việc skill này KHÔNG làm

- Không cung cấp/quản lý API key thay người dùng.
- Không mặc định model cố định vĩnh viễn — cập nhật `DEFAULT_MODEL`/`DEFAULT_TEXT_MODEL` trong script nếu Gemini đổi tên model, đừng để model cũ silently fail.
- Không tự động chạy khi không có `GEMINI_API_KEY` (trừ `extract_pdf_page.py`, không cần key).
- Không hard-code style-rules/brand identity của bất kỳ project cụ thể nào (khác các script gốc quan sát được, vốn có style-rules/GCS-upload/DB-insert cứng cho từng project) — mọi nội dung phong cách/output đích luôn do người gọi skill cung cấp, giữ skill portable.
- Không tự upload lên cloud storage hay ghi vào database — chỉ ghi file local, khác các pipeline gốc gắn với hạ tầng platform cụ thể.

## File đi kèm

- `scripts/generate_image.py` — CLI 3 chế độ (đơn lẻ/style-ref/batch với auto-anchor).
- `scripts/analyze_style.py` — vision-analysis, ảnh → mô tả phong cách text.
- `scripts/extract_pdf_page.py` — trích trang PDF thành PNG, không cần AI.
- `scripts/batch_manifest.example.json` — mẫu manifest cho chế độ batch.

## Giới hạn đã biết (v0.3.0)

- Model tên tại thời điểm viết (2026-07-26) — có thể đổi theo thời gian.
- Batch chưa hỗ trợ retry tự động khi 1 ảnh fail trong cùng lần chạy — chạy lại batch sẽ tự skip ảnh đã có và chỉ thử lại ảnh fail.
- Chưa có "style-chain thật" kiểu mỗi ảnh nối tiếp ảnh NGAY TRƯỚC nó (khác auto-anchor hiện tại, vốn cố định 1 anchor cho cả batch) — nếu cần drift phong cách có chủ đích qua một chuỗi dài, chưa hỗ trợ.
- Chưa hỗ trợ brand-identity generation (logo + icon + favicon từ 1 mô tả sản phẩm) như 1 lệnh riêng — hiện phải tự viết manifest batch tương đương.
