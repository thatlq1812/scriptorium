---
name: quality-eval
description: Chấm chất lượng một skill đã tạo bằng cách chạy thật trên ≥2 harness đã verify, so sánh with-skill vs baseline (không dùng skill), theo tiêu chí pass/fail cụ thể cho từng test case. Dùng sau khi skill-creator tạo xong một skill, trước khi registry được phép đánh dấu skill đó "sẵn sàng dùng". KHÔNG đánh giá bảo mật (đó là security-audit, bước 5 riêng biệt) — không gộp hai việc vào một lần chạy.
license: MIT
compatibility: Quy trình chạy trên harness đích của skill đang chấm — tối thiểu 2 harness đã verify trong `registry/skills.json` của skill đó. Chưa áp dụng thật lên skill nào của Scriptorium (v0.1.0) — thiết kế xong, chưa chạy case thật.
metadata:
  domain: meta
  task_type: review-qa
  risk_tier: N2
  pipeline_stage: 4
  source: self-authored
  elicited_from: "Grounded từ SkillsBench (arXiv 2602.12670 — methodology no-skill/curated/self-generated, deterministic verifiers, +16.2pp trung bình nhưng 16/84 task delta âm). Pattern baseline-comparison (with-skill vs without-skill) adapted từ github.com/anthropics/skills skill-creator (Apache-2.0, cleared qua license-compliance-check), bỏ phần phụ thuộc subagent/eval-viewer riêng của Claude Code để giữ harness-agnostic đúng nguyên tắc portable."
  version: 0.1.0
  adapted_from: "Baseline-comparison pattern từ github.com/anthropics/skills skills/skill-creator (Apache-2.0), cleared 2026-07-26"
---

# quality-eval

Trả lời 1 câu cho mỗi skill: **skill này có thật sự cải thiện kết quả so với không có nó, trên từng harness đã tuyên bố compatible?** Không chấm "skill viết có hay không" — chấm bằng kết quả tác vụ thật.

## Precondition

Skill đang chấm đã qua stage 3 (`skill-creator`), có `SKILL.md` hoàn chỉnh trong `skills/<id>/`, và registry entry có `quality_score: null`. Nếu skill chưa tồn tại, dừng — đây không phải bước tạo skill.

## Quy trình

### 1. Viết 2-3 test prompt thật

Dựa trên `description` (phần "khi nào dùng") của skill, viết prompt như người dùng thật sẽ gõ — cụ thể, có ngữ cảnh, không trừu tượng ("hãy dùng skill X" là prompt tệ; "tôi có file báo cáo Q3.pdf, cần tách ra từng phần theo chương để đọc riêng" là prompt tốt). Bao phủ: 1 case điển hình + 1 case biên (input khó hơn bình thường) + 1 case near-miss nếu skill dễ bị nhầm với skill khác trong registry.

### 2. Chạy with-skill và baseline, trên từng harness đã tuyên bố compatible

Với mỗi test prompt, trên MỖI harness trong `registry/skills.json.tags.harness_compatibility` của skill đó:
- **With-skill**: agent có quyền truy cập skill, thực hiện task.
- **Baseline**: cùng agent/model, cùng prompt, KHÔNG có skill — thực hiện task bằng khả năng sẵn có.

Tối thiểu 2 harness (đúng yêu cầu `docs/specs/STRATEGY_SPEC.md` §3 bước 4). Nếu skill mới chỉ verify 1 harness, quality-eval không chạy được đầy đủ — báo lại, không tự nới lỏng xuống 1 harness.

### 3. Chấm từng run theo tiêu chí cụ thể, không chấm cảm tính

Trước khi chạy, viết assertion cụ thể cho mỗi test case (vd "file output có đúng field X trong index.json", "không có bước nào agent tự bịa lệnh không tồn tại"). Assertion kiểm được bằng script thì viết script kiểm, không tự nhìn rồi đánh giá — nhanh hơn và nhất quán hơn giữa các lần chạy.

### 4. Tính delta, không chỉ pass/fail tuyệt đối

Với mỗi harness: `pass_rate(with_skill) - pass_rate(baseline)`. Ghi lại cả 2 con số, không chỉ delta — một skill có thể "pass 100% with-skill" nhưng baseline cũng pass 100% (skill không tạo khác biệt gì, dấu hiệu skill thừa hoặc mô tả sai chỗ cần dùng nó).

### 5. Verdict

- Delta dương trên MỌI harness đã test → `verdict: "pass"`.
- Delta ≤ 0 trên bất kỳ harness nào → `verdict: "needs-revision"`, quay lại `skill-creator` với feedback cụ thể (đừng chỉ nói "chưa tốt" — nói rõ test case nào fail và vì sao), không tự sửa SKILL.md trong quality-eval.
- SkillsBench cho thấy ngay cả curated skill cũng có ~19% task delta âm — verdict "needs-revision" là kết quả bình thường của quy trình, không phải thất bại của quality-eval.

### 6. Ghi kết quả vào registry

```json
"quality_score": {
  "harnesses_tested": ["claude-code", "..."],
  "test_cases": 3,
  "delta_pass_rate": { "claude-code": 0.67, "...": 0.33 },
  "verdict": "pass",
  "date": "YYYY-MM-DD"
}
```

`quality_score != null` là điều kiện CẦN (không đủ) để skill "sẵn sàng dùng" — còn cần `security_audit.status = "passed"` (bước 5).

## Việc quality-eval KHÔNG làm

- Không đánh giá bảo mật/injection — đó là `security-audit`, bước 5, chạy riêng.
- Không tự sửa SKILL.md khi verdict là "needs-revision" — bàn giao lại cho `skill-creator`.
- Không tự thêm harness vào `tags.harness_compatibility` chỉ vì test ở đó — harness compatibility được set khi skill *chạy được*, quality_score đo skill đó *chạy tốt tới đâu*, hai việc khác nhau.
