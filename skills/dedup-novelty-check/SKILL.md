---
name: dedup-novelty-check
description: Kiểm tra một skill ứng viên có trùng lặp đáng kể với skill đã có trong registry không, bằng script tính điểm overlap trên domain/task_type/mô tả — không suy đoán bằng mắt. Dùng ngay trước khi khởi động skill-creator cho một skill mới. KHÔNG dùng để đánh giá chất lượng hay license (đó là quality-eval và license-compliance-check).
license: MIT
compatibility: Script Python 3 thuần chuẩn thư viện (argparse/json/re), không cần cài dependency, không cần venv. Verify chạy sạch: Claude Code, Windows (2026-07-26, test cả case flagged và case an toàn trên registry thật).
metadata:
  domain: meta
  task_type: review-qa
  risk_tier: N1
  pipeline_stage: 8
  source: self-authored
  elicited_from: "Chưng cất từ quy tắc đã ghi trong registry/SCHEMA.md ('Nguyên tắc dedup/novelty-check', bước 9 pipeline STRATEGY_SPEC) — bước này trước đó là quy tắc thủ công, formalize thành script tính overlap thật, verify trên 8 skill hiện có của registry"
  version: 0.1.0
---

# dedup-novelty-check

Trả lời: **ứng viên này đã có skill nào trong registry phủ được ≥80% phạm vi chưa?** Tính bằng số, không phải cảm giác "nghe quen quen".

## Cách tính overlap

`scripts/check_dedup.py` — thuần thư viện chuẩn Python, không dependency:

```bash
python scripts/check_dedup.py \
  --domain <domain1> <domain2>... \
  --task-type <task_type1>... \
  --description "mô tả ngắn ứng viên (tiếng Việt hoặc Anh đều được)"
```

Công thức: `combined_score = 0.4 × domain_jaccard + 0.4 × task_type_jaccard + 0.2 × description_token_jaccard`, so với từng skill trong `registry/skills.json`. Trọng số nghiêng về tag (domain/task_type) vì đó là tín hiệu có cấu trúc, đáng tin hơn overlap từ vựng thô trong `elicited_from`.

Ngưỡng mặc định `0.8` (khớp "≥80% phạm vi" đã quy định ở `registry/SCHEMA.md`) — chỉnh qua `--threshold` nếu cần nhạy hơn/lỏng hơn cho một trường hợp cụ thể.

## Quy trình

1. Chạy script với domain/task_type/description dự kiến của ứng viên MỚI (trước khi viết SKILL.md thật).
2. Exit code `1` + danh sách FLAGGED → có skill trùng đáng kể. Ưu tiên mở rộng/versioning skill đó (tăng `version`, thêm tính năng) thay vì tạo skill song song — trừ khi có lý do rõ ràng để tách riêng (ghi lý do đó vào `elicited_from` của skill mới).
3. Exit code `0` → an toàn, bàn giao cho `skill-creator`.

## Giới hạn đã biết (v0.1.0)

- `description_token_jaccard` chỉ so token thô (không stemming, không đồng nghĩa) — hai mô tả cùng ý nhưng khác từ vựng hoàn toàn sẽ ra điểm thấp giả tạo. Trọng số 0.2 (thấp) cho phần này là có chủ đích, không dựa chủ yếu vào nó.
- Không phát hiện được overlap về *cách làm* (implementation) nếu domain/task_type/mô tả khác nhau nhưng logic bên trong giống hệt — chỉ bắt overlap ở tầng khai báo (registry), không đọc nội dung `SKILL.md` của skill khác.
