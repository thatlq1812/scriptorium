# Scriptorium

Hệ thống tạo, kiểm định chất lượng, audit bảo mật, và quản lý danh mục cho Agent Skill portable — không khóa vào một harness (Claude Code, Codex CLI, Kimi Code CLI, ...). Kế thừa bài học từ EduStation, không kế thừa khuôn của nó.

Bắt đầu từ [docs/README.md](docs/README.md) — navigation hub, dẫn vào kiến trúc, trạng thái thật, và SPEC chiến lược.

## Cấu trúc

- `docs/` — `MASTER_CONTEXT.md` (kiến trúc + quy chế tài liệu), `STATUS.md` (trạng thái thật), `DECISIONS_PENDING.md`, `specs/` (SPEC chính thức), `archive/` (lịch sử thảo luận/research thô).
- `skills/` — từng skill là một thư mục con chứa `SKILL.md` đúng 6-field spec của agentskills.io (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`).
- `registry/` — xương sống định danh đa trục (domain, task-type, risk-tier, harness-compatibility). Schema: `registry/SCHEMA.md`. Dữ liệu: `registry/skills.json`.

## Pipeline bootstrap (đang triển khai)

Research → Elicit tacit process → **skill_creator** → Quality evaluation (≥2 harness) → Security audit (stage riêng) → Skill scout/harvester → License-compliance check → Dedup/novelty-check → Registry.

Không đảo thứ tự. Không để agent tự sinh skill mà không có input elicited từ nguồn thật — SkillsBench đo self-generated skill "no benefit on average".

## Nguyên tắc không thương lượng

1. Bám đúng spec mở agentskills.io — không tự chế thêm field frontmatter ngoài chuẩn.
2. Quality và security là hai gate khác nhau, không gộp một bước review.
3. Không đánh dấu harness-compatible dựa trên tuyên bố của vendor — chỉ verify trực tiếp.
4. Một skill chạy tốt, audit sạch, dùng thật — quan trọng hơn mười skill nằm trong registry chưa ai dùng.

Chi tiết đầy đủ: `docs/specs/STRATEGY_SPEC.md`.
