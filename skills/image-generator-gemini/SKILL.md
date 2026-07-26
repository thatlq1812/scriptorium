---
name: image-generator-gemini
description: Tạo ảnh từ mô tả text bằng model ảnh của Gemini (google-genai SDK), dùng API key RIÊNG của người dùng — tùy chọn, không phải backend AI do Scriptorium quản lý. Dùng khi người dùng đã có sẵn Gemini API key và cần tạo ảnh minh họa/cover/asset từ mô tả. KHÔNG dùng nếu người dùng chưa có key riêng — skill này không cung cấp key thay, và không phải lối tắt để né nguyên tắc "Scriptorium không tích hợp AI backend" (xem ghi chú bên dưới).
license: MIT
compatibility: Cần Python 3.11+ + `google-genai` (bootstrap qua `python-env-bootstrap`) + biến môi trường `GEMINI_API_KEY` của chính người dùng. Verify chạy sạch: Claude Code, Windows (2026-07-26) — chỉ verify structural (import + error path khi thiếu key), CHƯA gọi API thật (cần key thật + owner cho phép phát sinh chi phí, chưa xin phép trong phiên này).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded từ pattern thật trong D:/elix/platform/scripts/gen/gen_illustrations.py (owner's own project): google-genai SDK, model gemini-3-pro-image-preview, generate_content(response_modalities=[\"IMAGE\"]), đọc GEMINI_API_KEY từ env. google-genai xác nhận Apache-2.0 qua PyPI JSON API. Tự viết script mới (không copy nguyên file owner), tổng quát hóa thành CLI 2 tham số."
  version: 0.1.0
---

# image-generator-gemini

Tạo ảnh từ prompt text, dùng Gemini image model qua key riêng của người dùng.

## Quan trọng — không mâu thuẫn với nguyên tắc "không tích hợp AI backend"

`docs/specs/STRATEGY_SPEC.md` §2 nói Scriptorium không tích hợp AI backend nào — nguyên tắc đó nói về **Scriptorium tự nó** không đứng giữa như một service gọi LLM hộ ai bằng credential của chính Scriptorium. Skill này khác bản chất: nó là instruction cho agent gọi API **bằng key của chính người dùng đang chạy skill** (bring-your-own-key), hoàn toàn tùy chọn (owner đánh dấu optional trong `docs/ROADMAP.md` mục 6) — giống một skill "gửi email qua SendGrid" dùng SendGrid key riêng của người dùng. Không phải Scriptorium cấp key, quản lý billing, hay bắt buộc dùng.

## Bootstrap môi trường

```bash
.\skills\python-env-bootstrap\scripts\bootstrap.ps1 -SkillDir skills\image-generator-gemini -PyVersion 3.12
```

## Dùng

```bash
export GEMINI_API_KEY="key-cua-ban"   # hoặc --api-key
python scripts/generate_image.py "mô tả ảnh cần tạo" output.png
```

## Việc skill này KHÔNG làm

- Không cung cấp/quản lý API key thay người dùng.
- Không mặc định model — nếu Gemini đổi tên model ảnh mới nhất, cập nhật `DEFAULT_MODEL` trong script, đừng để model cũ silently fail.
- Không tự động chạy khi không có `GEMINI_API_KEY` — báo lỗi rõ ràng, không thử fallback sang key khác hay backend khác.

## Giới hạn đã biết (v0.1.0)

- **Chưa verify bằng lệnh gọi API thật** — chỉ verify structural (script import đúng, xử lý đúng khi thiếu key). Gọi API thật tốn phí trên tài khoản người dùng; cần xin phép + key thật trước khi verify end-to-end. Không đánh dấu `harness_compatibility` cho tới khi verify thật.
- Model `gemini-3-pro-image-preview` là tên tại thời điểm viết (2026-07-26) — có thể đổi theo thời gian, kiểm tra lại nếu API báo lỗi "model not found".
