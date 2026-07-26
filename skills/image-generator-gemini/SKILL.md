---
name: image-generator-gemini
description: Tạo ảnh từ mô tả text bằng model ảnh của Gemini (google-genai SDK), dùng API key RIÊNG của người dùng — tùy chọn, không phải backend AI do Scriptorium quản lý. Hỗ trợ ảnh đơn lẻ, style-anchoring (dùng 1 ảnh tham chiếu để giữ nhất quán phong cách qua nhiều lần generate), và batch generation cả một bộ asset từ manifest JSON. Dùng khi người dùng đã có sẵn Gemini API key và cần tạo ảnh minh họa/cover/icon/bộ asset đồng bộ phong cách. KHÔNG dùng nếu người dùng chưa có key riêng — skill này không cung cấp key thay, và không phải lối tắt để né nguyên tắc "Scriptorium không tích hợp AI backend" (xem ghi chú bên dưới).
license: MIT
compatibility: Cần Python 3.11+ + `google-genai` (bootstrap qua `python-env-bootstrap`) + biến môi trường `GEMINI_API_KEY` của chính người dùng. Verify chạy sạch: Claude Code, Windows (2026-07-26) — verify THẬT bằng lệnh gọi API thật (model `gemini-3.1-flash-lite-image`, key test từ owner): ảnh đơn lẻ, batch 2 ảnh + skip-if-exists, style-ref anchoring — cả 3 đều xác nhận đúng bằng cách xem lại ảnh sinh ra.
metadata:
  domain: general
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded từ 2 pattern thật trong D:/elix/platform/scripts/gen/gen_illustrations.py (google-genai SDK, model ảnh, response_modalities IMAGE) VÀ D:/UNI/S9_SP26/MLN131/project/scripts/gen-images-v2.mjs + gen-slide-images.mjs (owner's own projects): batch generation với skip-if-exists + rate-limit delay, và style-ref anchoring (ảnh tham chiếu làm inlineData part + text instruction 'STRICT style reference'), cộng double-base64-decode fallback đã quan sát là bug fix thật trong code owner. Tự viết lại toàn bộ bằng Python, tổng quát hóa (bỏ nội dung style-rules đặc thù game của owner, chỉ giữ cơ chế)."
  version: 0.2.0
---

# image-generator-gemini

Tạo ảnh từ prompt text, dùng Gemini image model qua key riêng của người dùng — hỗ trợ 3 chế độ: đơn lẻ, style-anchored, batch.

## Quan trọng — không mâu thuẫn với nguyên tắc "không tích hợp AI backend"

`docs/specs/STRATEGY_SPEC.md` §2 nói Scriptorium không tích hợp AI backend nào — nguyên tắc đó nói về **Scriptorium tự nó** không đứng giữa như một service gọi LLM hộ ai bằng credential của chính Scriptorium. Skill này khác bản chất: nó là instruction cho agent gọi API **bằng key của chính người dùng đang chạy skill** (bring-your-own-key), hoàn toàn tùy chọn (owner đánh dấu optional trong `docs/ROADMAP.md` mục 6) — giống một skill "gửi email qua SendGrid" dùng SendGrid key riêng của người dùng. Không phải Scriptorium cấp key, quản lý billing, hay bắt buộc dùng.

## Bootstrap môi trường

```bash
.\skills\python-env-bootstrap\scripts\bootstrap.ps1 -SkillDir skills\image-generator-gemini -PyVersion 3.12
```

## Ảnh đơn lẻ

```bash
export GEMINI_API_KEY="key-cua-ban"   # hoặc --api-key
python scripts/generate_image.py "mô tả ảnh cần tạo" output.png
```

## Style-anchoring — giữ nhất quán phong cách qua nhiều ảnh

```bash
python scripts/generate_image.py "mô tả ảnh mới" output2.png --style-ref output.png
```

`--style-ref` gửi kèm ảnh tham chiếu + instruction "STRICT style reference" trước prompt chính — model match palette/lighting/line-weight của ảnh tham chiếu khi vẽ chủ thể mới. Dùng khi cần một bộ ảnh trông "cùng một gia đình" (vd icon set, cover series) thay vì mỗi ảnh một phong cách ngẫu nhiên.

## Batch — tạo cả bộ asset từ manifest

```bash
python scripts/generate_image.py --batch manifest.json --out-dir assets/
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

Đặc điểm: **skip-if-exists** (chạy lại batch không sinh lại ảnh đã có — an toàn khi batch fail giữa chừng, chạy lại tiếp tục từ chỗ dừng), **rate-limit delay** giữa mỗi request (mặc định 3s, chỉnh qua `--delay`), style_ref trong manifest áp dụng cho TOÀN BỘ ảnh trong batch (đồng bộ phong cách cả set).

## Việc skill này KHÔNG làm

- Không cung cấp/quản lý API key thay người dùng.
- Không mặc định model cố định vĩnh viễn — nếu Gemini đổi tên model ảnh mới nhất, cập nhật `DEFAULT_MODEL` trong script, đừng để model cũ silently fail. Model nhẹ hơn (`gemini-3.1-flash-lite-image`) dùng tốt cho test/draft, model `pro` cho ảnh chất lượng cuối.
- Không tự động chạy khi không có `GEMINI_API_KEY` — báo lỗi rõ ràng, không thử fallback sang key khác hay backend khác.
- Không hard-code style-rules nội dung của bất kỳ project cụ thể nào (khác pattern gốc quan sát được ở dự án MLN131 của owner, nơi style rules là text cứng cho một game cụ thể) — cơ chế style-ref/anchoring ở đây là tổng quát, nội dung phong cách luôn do người gọi skill cung cấp.

## File đi kèm

- `scripts/generate_image.py` — CLI 3 chế độ (đơn lẻ/style-ref/batch).
- `scripts/batch_manifest.example.json` — mẫu manifest cho chế độ batch.

## Giới hạn đã biết (v0.2.0)

- Model `gemini-3-pro-image-preview`/`gemini-3.1-flash-lite-image` là tên tại thời điểm viết (2026-07-26) — có thể đổi theo thời gian.
- Batch chưa hỗ trợ retry tự động khi 1 ảnh fail (chỉ log FAIL và tiếp tục) — chạy lại batch sẽ tự skip ảnh đã có và chỉ thử lại ảnh fail, nhưng không phải retry trong cùng 1 lần chạy.
