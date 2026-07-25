# Scriptorium

Hệ thống tạo, kiểm định chất lượng, audit bảo mật, và quản lý danh mục cho Agent Skill portable — không khóa vào một harness (Claude Code, Codex CLI, Kimi Code CLI, ...). Kế thừa bài học từ EduStation, không kế thừa khuôn của nó.

Bối cảnh và toàn bộ quyết định/nghiên cứu đã dẫn tới kiến trúc này: xem `docs/`.

## Cấu trúc

- `docs/` — tài liệu nền: bài học EduStation (`handoff.md`, `note.md`), thảo luận định hướng và báo cáo nghiên cứu sâu (`conservation.md`, `raw_research.md`, `full_content_and_research.md`). Đọc trước khi làm việc trên bất kỳ skill nào.
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

Chi tiết đầy đủ: `docs/handoff.md`.
