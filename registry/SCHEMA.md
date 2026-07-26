# Registry Schema

Đăng ký (registry) là xương sống định danh của Scriptorium: mọi skill đi qua pipeline bootstrap đều phải có một entry trong `registry/skills.json` trước khi coi là "phát hành nội bộ". Registry dùng tag đa trục, không ép vào một category cứng — một skill có thể mang nhiều tag trên cùng một trục và trên nhiều trục cùng lúc.

Tham chiếu quyết định: `docs/specs/STRATEGY_SPEC.md` §3 (bước 9) và §4.

## Bốn trục tag (mọi skill gắn ≥1 tag mỗi trục)

- **domain** — trục ngành/nghề. Tham khảo trực tiếp occupation group của SkillsMP thay vì tự nghĩ taxonomy riêng. Hai giá trị đặc biệt: `meta` cho skill vận hành chính Scriptorium (skill-creator, quality-eval, security-audit...); `general` cho skill task-type thuần túy, hữu ích như nhau ở mọi ngành (vd. document-ai-structurer — chuyển đổi tài liệu không thiên về domain nào).
- **task-type** — trục loại tác vụ, cắt ngang mọi ngành: `research`, `document-conversion`, `drafting`, `review-qa`, `coordination`.
- **risk-tier** — kế thừa tinh thần N1–N5 của EduStation, tái áp dụng thành mức rủi ro đầu ra/liability: `N1` (thấp, ví dụ tra cứu/chuyển đổi định dạng) đến `N5` (cao, ví dụ soạn hợp đồng/duyệt luật — bắt buộc human gate).
- **harness-compatibility** — danh sách harness đã **verify chạy sạch thật**, không phải suy đoán từ showcase vendor. Giá trị hợp lệ chỉ được thêm sau khi test trực tiếp (xem `docs/archive/pre-spec-2026-07-26/handoff.md` mục 5).

## Field bắt buộc của một entry

| Field | Kiểu | Ghi chú |
|---|---|---|
| `skill_id` | string | Định danh gốc, bất biến, trùng tên thư mục trong `skills/`. |
| `version` | string (semver) | Tăng khi nội dung SKILL.md thay đổi có ý nghĩa. |
| `source` | object | `{ "type": "self-authored" \| "harvested", "repo_url"?: string, "commit"?: string, "adapted_from"?: { "repo_url", "path", "license", "cleared_by" } }`. Nếu `harvested`, `repo_url` + `commit` bắt buộc. `adapted_from` dùng khi `type = self-authored` nhưng có pattern/ý tưởng cụ thể mượn từ nguồn ngoài đã qua license-compliance-check (không phải harvest nguyên khối) — vẫn phải qua check trước khi ghi. |
| `license` | string | SPDX identifier (`MIT`, `Apache-2.0`, ...). Bắt buộc qua license-compliance check nếu `source.type = harvested` HOẶC `source.adapted_from` có giá trị. |
| `tags.domain` | string[] | ≥1 giá trị. |
| `tags.task_type` | string[] | ≥1 giá trị. |
| `tags.risk_tier` | string | Đúng 1 giá trị N1–N5. |
| `tags.harness_compatibility` | string[] | Có thể rỗng nếu chưa qua quality-eval; không được suy đoán. |
| `quality_score` | object \| null | Kết quả từ quality-eval loop (bước 4 pipeline). `null` nếu chưa chạy. |
| `security_audit` | object | `{ "status": "pending" \| "passed" \| "failed", "date": string \| null }`. Không có skill nào được coi là sẵn sàng dùng khi `status != "passed"`. |
| `dependencies` | string[] | Script/tool đi kèm skill (nếu có). |
| `elicited_from` | string | Nguồn tri thức ngầm đã elicit trước khi tạo skill — bắt buộc khác rỗng, theo nguyên tắc "no self-generated-only" (`docs/specs/STRATEGY_SPEC.md` §7 điểm 4). |

## Nguyên tắc dedup/novelty-check

Trước khi khởi động skill-creator cho một ứng viên mới, tra `registry/skills.json` theo `tags` liên quan. Nếu một skill hiện có phủ ≥80% phạm vi ứng viên mới, ưu tiên mở rộng/versioning skill đó thay vì tạo entry song song.
