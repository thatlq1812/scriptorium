# Status — Scriptorium

| Last Updated | Status |
| --- | --- |
| 2026-07-26 | 7 skill đã viết. Toàn bộ 5 skill trước đã qua `security-audit` (đều `passed`), chưa skill nào có `quality_score` (stage 4 chưa chạy trên skill nào) — nên chưa skill nào "sẵn sàng dùng" chính thức dù đã dùng thật trong session. Mọi thứ dưới đây verify trực tiếp từ `registry/skills.json` + `skills/`. |

## Skill đã tồn tại

| skill_id | version | risk_tier | quality_score | security_audit | Sẵn sàng dùng? |
| --- | --- | --- | --- | --- | --- |
| `skill-creator` | 0.2.0 | N2 | `null` | `passed` | **Chưa chính thức** — security-audit sạch, nhưng chưa qua stage 4 (quality eval ≥2 harness). |
| `document-ai-structurer` | 0.1.0 | N1 | `null` | `passed` | **Chưa chính thức** — smoke test PDF thật OK, security-audit sạch (external fetch Docling đã khai báo), chưa qua stage 4. |
| `python-env-bootstrap` | 0.1.0 | N1 | `null` | `passed` (chấp nhận rủi ro có ghi chú) | **Chưa chính thức** — verify chạy đúng Windows/PowerShell. Security-audit ghi nhận blind-trust pattern (`curl\|sh`/`irm\|iex` từ astral.sh) là rủi ro chấp nhận được (nguồn chính chủ, đã khai báo), chưa qua stage 4. |
| `license-compliance-check` | 0.2.0 | N2 | `null` | `passed` | **Chưa chính thức** — verify chạy thật trên anthropics/skills, security-audit sạch, chưa qua stage 4. |
| `quality-eval` | 0.1.0 | N2 | `null` | `passed` | **Chưa chính thức** — thiết kế xong (v0.1.0), chưa áp dụng lên skill thật nào, security-audit sạch (chưa có script). |
| `security-audit` | 0.1.0 | N2 | `null` | `passed` (self-audit) | **Chưa chính thức** — đã áp dụng thật lên 5 skill trên (self-audit), chưa qua stage 4. |
| `scout-harvester` | 0.1.0 | N1 | `null` | `passed` | **Chưa chính thức** — chưng cất từ 3 lần chạy thật trong phiên (Docling, uv, anthropics/skills), chưa qua stage 4. |

Nguồn: `registry/skills.json`. Nếu số liệu ở đây khác `registry/skills.json`, registry thắng — file này có thể lỗi thời.

## Pipeline stage — cái gì có skill vận hành, cái gì chưa

| Stage | Skill vận hành | Trạng thái |
| --- | --- | --- |
| 1. Research | — | Chưa có skill; đã chạy thủ công nhiều lần (owner + Claude) |
| 2. Elicit tacit process | — | Chưa có skill; đã chạy thủ công cho từng skill hiện có |
| 3. skill-creator | `skills/skill-creator/SKILL.md` | Có |
| 4. Quality evaluation | `skills/quality-eval/SKILL.md` | Có — thiết kế xong, chưa áp dụng lên skill thật nào |
| 5. Security audit | `skills/security-audit/SKILL.md` | Có — đã áp dụng thật lên 5 skill (self-audit) |
| 6. Scout/harvester | `skills/scout-harvester/SKILL.md` | Có |
| 7. License-compliance check | `skills/license-compliance-check/SKILL.md` | Có |
| 8. Dedup/novelty-check | — | Chưa xây (quy tắc có trong `registry/SCHEMA.md`, chưa tự động hóa) |
| 9. Registry | `registry/SCHEMA.md` + `registry/skills.json` | Có, 7 entry |

Bộ xương pipeline (stage 3-7, 9) đã đủ skill vận hành. Còn thiếu: stage 1/2 (chưa cần skill hóa, vẫn làm thủ công tốt), stage 8 (dedup tự động).

## Sổ nợ pháp lý (license debt)

Trống — chưa skill nào có `license_debt != null`. Bắt buộc rà lại toàn bộ bảng này trước khi rời giai đoạn bootstrap (trước Phase 2 vertical pháp lý). Xem `docs/specs/STRATEGY_SPEC.md` §7 điểm 5, `registry/SCHEMA.md`.

| skill_id | Nguồn | Lý do nợ | Kế hoạch thay thế | Ngày |
| --- | --- | --- | --- | --- |

## Hạ tầng

- Git repo: khởi tạo 2026-07-26, chưa có remote.
- AI backend: không có, theo thiết kế — Scriptorium không tích hợp Elixverse hay bất kỳ AI API nào (`docs/specs/STRATEGY_SPEC.md` §2, §6).
