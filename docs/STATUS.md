# Status — Scriptorium

| Last Updated | Status |
| --- | --- |
| 2026-07-26 | Bootstrap pipeline stage 3 (skill_creator) có 1 skill đã viết, chưa qua stage 4/5. Mọi thứ dưới đây verify trực tiếp từ `registry/skills.json` + `skills/`. |

## Skill đã tồn tại

| skill_id | version | risk_tier | quality_score | security_audit | Sẵn sàng dùng? |
| --- | --- | --- | --- | --- | --- |
| `skill_creator` | 0.1.0 | N2 | `null` | `pending` | **Chưa** — chưa qua stage 4 (quality eval ≥2 harness) và stage 5 (security audit). Chỉ mới verify chạy trên Claude Code. |

Nguồn: `registry/skills.json`. Nếu số liệu ở đây khác `registry/skills.json`, registry thắng — file này có thể lỗi thời.

## Pipeline stage — cái gì có skill vận hành, cái gì chưa

| Stage | Skill vận hành | Trạng thái |
| --- | --- | --- |
| 1. Research | — | Chưa có skill; đã chạy thủ công 1 lần (owner + Claude) cho chính Scriptorium |
| 2. Elicit tacit process | — | Chưa có skill; đã chạy thủ công 1 lần cho `skill_creator` |
| 3. skill_creator | `skills/skill_creator/SKILL.md` | Có |
| 4. Quality evaluation | — | Chưa xây |
| 5. Security audit | — | Chưa xây |
| 6. Scout/harvester | — | Chưa xây |
| 7. License-compliance check | — | Chưa xây |
| 8. Dedup/novelty-check | — | Chưa xây (quy tắc có trong `registry/SCHEMA.md`, chưa tự động hóa) |
| 9. Registry | `registry/SCHEMA.md` + `registry/skills.json` | Có, 1 entry |

## Hạ tầng

- Git repo: khởi tạo 2026-07-26, chưa có remote.
- AI backend: không có, theo thiết kế — Scriptorium không tích hợp Elixverse hay bất kỳ AI API nào (`docs/specs/STRATEGY_SPEC.md` §2, §6).
