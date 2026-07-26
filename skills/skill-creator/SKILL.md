---
name: skill-creator
description: Chuẩn hóa tri thức thủ tục đã được elicit từ một nguồn thật (chuyên gia, hoặc tacit knowledge của owner) cộng với research đã grounding, thành một Agent Skill portable tuân đúng spec mở agentskills.io (6-field frontmatter). Dùng khi input elicited-process + research đã sẵn sàng cho một quy trình lặp lại, cụ thể. KHÔNG dùng để tự suy luận ra một skill mới khi chưa có input elicited/research — self-generated skill không qua elicit đã được đo là "no benefit on average" (SkillsBench).
license: MIT
compatibility: Portable theo spec mở agentskills.io (frontmatter 6 field, không mở rộng). Verify chạy sạch: Claude Code (2026-07-26). Chưa verify: OpenAI Codex CLI, Kimi Code CLI, Antigravity CLI — không được đánh dấu compatible cho tới khi test trực tiếp.
metadata:
  domain: meta
  task_type: skill-authoring
  risk_tier: N2
  pipeline_stage: 3
  source: self-authored
  elicited_from: "Owner tacit knowledge từ EduStation postmortem (docs/archive/pre-spec-2026-07-26/handoff.md) + deep research session 2026-07-26, chưng cất vào docs/specs/STRATEGY_SPEC.md"
  version: 0.2.0
  adapted_from: "Pattern 'pushy description' + trigger eval set (should-trigger/should-not-trigger) adapted từ github.com/anthropics/skills skills/skill-creator (Apache-2.0), cleared qua skills/license-compliance-check ngày 2026-07-26. Đã diễn đạt lại theo ngôn ngữ/quy chế riêng của Scriptorium, không copy nguyên văn."
---

# skill-creator

Meta-skill sinh ra `SKILL.md` cho một skill khác trong Scriptorium. Đây là bước 3 trong pipeline bootstrap (`docs/specs/STRATEGY_SPEC.md` §3) — đứng SAU research và elicit tacit process, KHÔNG đứng trước.

## Precondition — kiểm tra trước khi chạy

Trước khi viết bất kỳ dòng SKILL.md nào, xác nhận cả hai điều kiện sau đã có, và ghi rõ nguồn:

1. **Elicited tacit process** — quy trình đã được rút ra từ một nguồn thật (chuyên gia thực hành, hoặc chính owner của Scriptorium mô tả kinh nghiệm cụ thể), không phải suy luận của model. Nếu chưa có, DỪNG lại — quay về bước elicit, không tự bịa quy trình rồi coi là input hợp lệ.
2. **Research đã grounding** — nguồn tham chiếu kiểm chứng được (tài liệu, benchmark, luật, tiêu chuẩn ngành), không phải kiến thức nội suy không kiểm chứng.

Nếu thiếu một trong hai, output của bước này rơi vào nhóm "self-generated skill" — đã được SkillsBench đo là không cải thiện gì so với không có skill. Không tạo skill trong tình trạng đó.

## Bám đúng 6 field spec — không tự chế thêm field

Frontmatter chỉ có đúng 6 key: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Mọi field riêng của Scriptorium (domain, task_type, risk_tier, pipeline_stage, elicited_from, harness_verified...) đi vào trong `metadata`, không bao giờ ở cấp top-level.

- `name` — bắt buộc, ≤64 ký tự, chỉ chữ thường/số/hyphen, PHẢI trùng tên thư mục cha trong `skills/`.
- `description` — bắt buộc, ≤1024 ký tự. Nêu rõ CẢ hai: skill làm gì, VÀ khi nào nên dùng / khi nào không nên dùng (giúp agent chọn đúng skill giữa nhiều skill có sẵn). Đây là cơ chế trigger chính — agent tiêu thụ quyết định có dùng skill hay không chỉ dựa vào `description` (chưa đọc thân bài). Xu hướng chung là **under-trigger** (agent bỏ qua skill lẽ ra nên dùng): viết description hơi "đẩy mạnh" thay vì trung tính — nêu rõ các biến thể ngữ cảnh/cách diễn đạt khác nhau mà người dùng có thể gõ, không chỉ 1 câu mẫu duy nhất. Trước khi chốt description, tự sinh 8-10 câu hỏi "nên trigger" + 8-10 câu "không nên trigger" (đặc biệt near-miss — câu hỏi dùng từ khóa gần giống nhưng thực ra cần skill khác) và tự kiểm description có phân biệt đúng không; sửa nếu sai.
- `license` — SPDX identifier. Nếu skill harvested từ nguồn ngoài, license phải khớp license gốc và đã qua license-compliance check (bước 7 pipeline) — không tự ý đổi sang MIT.
- `compatibility` — ≤500 ký tự. Chỉ liệt kê harness ĐÃ verify chạy thật. Harness chưa test thì không được liệt kê, kể cả khi vendor showcase nói có hỗ trợ (xem `docs/archive/pre-spec-2026-07-26/raw_research.md` §1 — Kimi Code CLI không có trong showcase chính thức dù nhiều nguồn thứ cấp nói có).
- `metadata` — map key-value tự do, dùng tối thiểu 5 field chuẩn của Scriptorium: `domain`, `task_type`, `risk_tier` (N1–N5, theo `registry/SCHEMA.md`), `source` (`self-authored` hoặc `harvested`), `elicited_from` (mô tả ngắn nguồn tri thức đã elicit — trường này không được để rỗng).
- `allowed-tools` — đánh dấu Experimental trong spec. Chỉ thêm khi có lý do an toàn cụ thể để giới hạn tool (ví dụ skill risk-tier cao không nên có quyền ghi file tùy ý). Không thêm mặc định "cho chắc".

## Ràng buộc cấu trúc

- Toàn bộ SKILL.md < 500 dòng.
- Phần instructions (thân bài sau frontmatter) < 5000 token — nếu quy trình dài, tách phần chi tiết ra file phụ trong cùng thư mục skill và reference từ SKILL.md (progressive disclosure), không nhồi hết vào một file.
- Không viết theo lối kể chuyện — viết theo lối instruction agent khác có thể theo mà không cần hỏi lại.

## Việc skill-creator KHÔNG làm

- Không tự chấm chất lượng skill vừa tạo — đó là bước 4 (quality evaluation loop), chạy riêng, trên ≥2 harness đã verify.
- Không tự audit bảo mật skill vừa tạo — đó là bước 5 (security audit), một pipeline stage riêng biệt, không gộp chung với bước 4 (`docs/specs/STRATEGY_SPEC.md` §7 điểm 2).
- Không tự quyết định skill đã "sẵn sàng dùng" — trạng thái đó chỉ được set khi `registry/skills.json` có `quality_score` khác null VÀ `security_audit.status = "passed"`.

## Output của skill-creator

1. Thư mục `skills/<name>/SKILL.md` (và file phụ nếu cần progressive disclosure) đúng 6-field spec.
2. Một entry nháp cho `registry/skills.json` theo đúng field trong `registry/SCHEMA.md`, với `quality_score: null` và `security_audit.status: "pending"` — không được tự set các field này thành đã pass.
3. Nếu ứng viên gần trùng một skill đã có trong registry (≥80% phạm vi), báo lại thay vì tạo entry song song — dedup/novelty-check là bước 8, chạy trước khi bước này bắt đầu tạo nội dung mới.
