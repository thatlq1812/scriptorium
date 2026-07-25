# Status — Scriptorium

| Last Updated | Status |
| --- | --- |
| 2026-07-26 | 2 skill đã viết (`skill-creator` từ stage 3, `document-ai-structurer` — skill domain/task-type thật đầu tiên). Cả hai chưa qua stage 4/5. Mọi thứ dưới đây verify trực tiếp từ `registry/skills.json` + `skills/`. |

## Skill đã tồn tại

| skill_id | version | risk_tier | quality_score | security_audit | Sẵn sàng dùng? |
| --- | --- | --- | --- | --- | --- |
| `skill-creator` | 0.1.0 | N2 | `null` | `pending` | **Chưa** — chưa qua stage 4 (quality eval ≥2 harness) và stage 5 (security audit). Chỉ mới verify chạy trên Claude Code. |
| `document-ai-structurer` | 0.1.0 | N1 | `null` | `pending` | **Chưa** — smoke test 1 PDF thật thành công (Claude Code), chưa qua stage 4/5 chính thức, chưa test DOCX/PPTX/XLSX/ảnh scan. Cần Python + `docling` (bootstrap venv riêng, xem `skills/document-ai-structurer/SKILL.md`). |

Nguồn: `registry/skills.json`. Nếu số liệu ở đây khác `registry/skills.json`, registry thắng — file này có thể lỗi thời.

## Pipeline stage — cái gì có skill vận hành, cái gì chưa

| Stage | Skill vận hành | Trạng thái |
| --- | --- | --- |
| 1. Research | — | Chưa có skill; đã chạy thủ công 1 lần (owner + Claude) cho chính Scriptorium |
| 2. Elicit tacit process | — | Chưa có skill; đã chạy thủ công 1 lần cho `skill-creator` |
| 3. skill-creator | `skills/skill-creator/SKILL.md` | Có |
| 4. Quality evaluation | — | Chưa xây |
| 5. Security audit | — | Chưa xây |
| 6. Scout/harvester | — | Chưa xây |
| 7. License-compliance check | — | Chưa xây |
| 8. Dedup/novelty-check | — | Chưa xây (quy tắc có trong `registry/SCHEMA.md`, chưa tự động hóa) |
| 9. Registry | `registry/SCHEMA.md` + `registry/skills.json` | Có, 1 entry |

## Hạ tầng

- Git repo: khởi tạo 2026-07-26, chưa có remote.
- AI backend: không có, theo thiết kế — Scriptorium không tích hợp Elixverse hay bất kỳ AI API nào (`docs/specs/STRATEGY_SPEC.md` §2, §6).
