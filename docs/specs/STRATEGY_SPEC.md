# Strategy Spec — Scriptorium

| Version | Date | Author | Description |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-26 | Claude (chưng cất từ thảo luận + research với owner) | Bản SPEC gốc đầu tiên, chưng cất từ `docs/archive/pre-spec-2026-07-26/` (transcript thảo luận + báo cáo nghiên cứu sâu), đã sửa số liệu lỗi thời và một mô tả sai về Elixverse (xác nhận bằng cách đọc trực tiếp code `D:/elix/platform`). |

---

## 1. Vấn đề & quyết định pivot

EduStation (`D:/elix/edustation`) — app agentic "Claude Code cho giáo viên Việt Nam" — không thất bại về kỹ thuật (M1-M3: engine, agentic loop, tool dispatcher đã "substantially landed"). Nó chết vì **governance-trước-traction**: đầu tư quá sâu vào một vertical duy nhất (18 R-rules, 5 non-negotiables, corpus pháp lý VN vendored đầy đủ) trước khi có pilot thật với người dùng (M4) chạy.

**Luận điểm cốt lõi dẫn tới pivot**: lớp harness/CLI agent đang bị hàng hóa hóa nhanh. Bằng chứng (giữa 2026):
- Grok Build (xAI, Apache 2.0) công khai port tool implementation từ `openai/codex` và `sst/opencode` — chính các hãng lớn cũng không viết harness từ đầu.
- Kimi Code CLI (MIT), Grok Build (Apache 2.0), Codex CLI (Apache 2.0), OpenCode, Aider đều mở, đều hỗ trợ Agent Skills + MCP + subagents + hooks.
- Agent Skills / `SKILL.md` đã là **chuẩn mở cross-vendor thật** — Anthropic công bố 18/12/2025 tại agentskills.io, showcase chính thức liệt kê **~44 nền tảng adopter** giữa 2026 (không phải "20-40+" như ước lượng ban đầu).

**Quyết định**: Phase 1 = xây hệ thống tạo/kiểm thử/audit/quản lý skill (Scriptorium). KHÔNG xây app/CLI/harness riêng. Giá trị dịch chuyển lên lớp tri thức (skill) và lớp kiểm định — chỗ mà cả ngành thừa nhận chưa giải xong (xem §3).

## 2. Phạm vi (scope) & non-goals

**Đang làm**: hệ thống tạo, kiểm thử chất lượng, audit bảo mật, và quản lý danh mục (registry) cho Agent Skill portable, tuân spec mở agentskills.io, không khóa vào một harness.

**KHÔNG làm** (ít nhất chưa phải bây giờ):
- Không tự xây app/CLI/harness agent riêng — skill chạy trên hệ sinh thái ~44 platform sẵn có.
- Không làm "chatbot tra luật" ở vertical pháp lý — thị trường VN đã đông (aitracuuluat.vn, AI Luật LuatVietnam, LEXcentra, CLS/CMC, Trợ Lý Luật, EmLaw). Scriptorium định vị ở **lớp meta**: sản xuất + kiểm định + audit skill pháp lý portable.
- Không để agent tự sinh skill mà không có input elicited từ nguồn thật — SkillsBench (arXiv 2602.12670) đo self-generated skill "no benefit on average", trong khi curated skill (có human-curated input) đạt +16.2pp pass rate trung bình.

## 3. Bootstrap pipeline (9 bước, thứ tự không đảo)

| # | Bước | Mục đích | Trạng thái (2026-07-26) |
| --- | --- | --- | --- |
| 1 | Research | Thu thập thông tin, source grounding | Đã chạy 1 lần cho chính Scriptorium (kết quả: file này + archive) |
| 2 | Elicit tacit process | Rút quy trình từ nguồn thật (chuyên gia hoặc owner) | Đã làm cho `skill_creator` (elicited từ owner qua EduStation postmortem) |
| 3 | **skill_creator** | Sinh `SKILL.md` đúng 6-field spec từ input (1)+(2) | Tự thân đã tồn tại: `skills/skill_creator/SKILL.md` |
| 4 | Quality evaluation loop | Chấm chất lượng qua tác vụ thật, ≥2 harness đã verify | Chưa xây skill cho bước này |
| 5 | Security / injection audit | Stage riêng biệt, đa lớp (static + LLM semantic + runtime), đối chiếu OWASP Agentic Skills Top 10 | Chưa xây skill cho bước này |
| 6 | Skill scout/harvester | Tìm + phân tích sâu skill có sẵn trong hệ sinh thái ngoài | Chưa xây skill cho bước này |
| 7 | License-compliance check | Bắt buộc ngay sau (6), trước khi vào (3) cho skill harvested | Chưa xây skill cho bước này |
| 8 | Dedup / novelty-check | Tra registry trước khi tạo skill mới | Quy tắc đã ghi trong `registry/SCHEMA.md`, chưa có skill tự động hóa |
| 9 | Registry đa trục | Xương sống định danh | `registry/SCHEMA.md` + `registry/skills.json` đã tồn tại, 1 entry (`skill_creator`) |

Không đảo thứ tự (1)→(2)→(3). Một skill chưa qua đủ (4) và (5) không được coi là "sẵn sàng dùng", bất kể deadline.

## 4. Registry — taxonomy đa trục

4 trục bắt buộc mỗi skill: **domain** (tham khảo occupation group của SkillsMP, không tự nghĩ taxonomy riêng), **task-type** (research / document-conversion / drafting / review-qa / coordination — cắt ngang mọi domain), **risk-tier** (N1–N5, kế thừa tinh thần EduStation nhưng chỉ là 1 field khai báo tại skill-declaration time, KHÔNG phải một enforcement engine riêng — xem `docs/archive` khảo sát EduStation), **harness-compatibility** (chỉ liệt kê harness đã verify chạy thật, không suy đoán từ showcase vendor). Field đầy đủ: `registry/SCHEMA.md`.

## 5. Vertical thử nghiệm đầu tiên: pháp lý Việt Nam

Flagship dự kiến, phân theo risk-tier: tra luật + chuyển statute→markdown (N1-N2, risk thấp, làm trước) → soạn công văn/review văn bản (trung bình) → soạn hợp đồng/duyệt luật (N4-N5, risk cao, **bắt buộc human-gate**, làm sau).

Bắt buộc kèm theo: citation-grounding (verify entity + relation preservation về văn bản gốc trước khi trả lời; dưới ngưỡng → re-retrieve hoặc human review) và versioning văn bản luật (theo dõi outdated norms — luật bị bãi bỏ). Căn cứ: Stanford RegLab/HAI "Hallucination-Free?" (arXiv 2405.20362) — Lexis+ AI hallucinate ~17%, Westlaw AI-Assisted Research ~33%, GPT-4 ~43% trên 202 truy vấn preregistered; tiền lệ *Mata v. Avianca, Inc.*, 678 F. Supp. 3d 443 (S.D.N.Y. 2023) — phạt $5,000 theo Rule 11 vì 6 vụ án bịa do ChatGPT sinh.

## 6. Elixverse (`D:/elix/platform`) — gate trước khi dùng làm backend agent loop

**Sửa mô tả cũ**: Elixverse KHÔNG phải "OpenAI-compatible API" — là API riêng, đa provider (Gemini/OpenAI/Anthropic), router tự thiết kế cấu trúc kiểu OpenAI-style, không theo schema OpenAI chuẩn. Xác nhận trực tiếp từ code + doc ngày 2026-07-26 (xem memory `project-platform-elixverse-status`).

**Xác nhận đúng và vẫn là blocker thật**: không có spend cap/scope riêng theo key (`elix_sk_...` toàn quyền như tài khoản chủ). Track 2 (multi-tenancy cost isolation, RPM/TPM theo token) bị hoãn, phụ thuộc Redis chưa triển khai đủ. → Trước khi cho bất kỳ skill nào của Scriptorium (vd. quality-eval loop) gọi Elixverse trong một agent loop tự động dài hơi, cần platform team giải quyết spend-cap + scoped key trước — điều kiện tiên quyết, không phải nice-to-have.

## 7. Nguyên tắc không thương lượng

1. Bám đúng 6-field spec mở agentskills.io (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`) — field riêng của Scriptorium luôn nằm trong `metadata`.
2. Quality evaluation và security audit là hai gate khác nhau — không gộp một bước review (pattern-matching scanner đơn lớp đã được Snyk chứng minh bỏ sót phần lớn tấn công nghiêm trọng).
3. Không đánh dấu harness-compatible dựa trên tuyên bố vendor/showcase — chỉ verify trực tiếp.
4. Không tự động hóa hoàn toàn khâu tạo skill — bắt buộc elicit từ nguồn thật trước `skill_creator` (self-generated skill "no benefit on average" — SkillsBench).
5. Harvest từ nguồn ngoài luôn qua license-compliance check trước khi chạm skill_creator, không có ngoại lệ "chỉ tham khảo nội bộ".
6. Một skill chạy tốt, audit sạch, dùng thật — quan trọng hơn mười skill nằm trong registry chưa ai dùng.

## 8. Nguồn — số liệu đã xác thực (không dùng số trong archive nếu khác ở đây)

- Adoption Agent Skills: **~44 nền tảng** (agentskills.io showcase, giữa 2026), không phải "20-40+".
- SkillsMP: **~2.3M skills**, 23 occupation group, 867 job category (không phải 1.6M — số cũ).
- Skills.sh (Vercel): **~670k skill listing** (6/2026, rywalker.com), không phải "~600k".
- Bỏ hẳn con số "chất lượng trung bình 6.2/12" — không khớp benchmark chuẩn nào tìm được. Dùng thay: Arcade.dev SkillBench — **73% skill "elevated safety risk"**; Snyk ToxicSkills — **36.82% skill có ≥1 lỗ hổng**, 13.4% critical.
- SkillsBench (arXiv 2602.12670): curated skill +16.2pp pass rate trung bình (dao động +4.5pp đến +51.9pp theo domain); self-generated skill "no benefit on average".
- Elixverse: sửa "OpenAI-compatible" → "API riêng, đa provider, cấu trúc kiểu OpenAI-style" (verify code 2026-07-26).

Toàn văn nguồn thứ cấp và các con số/giả định chưa xác thực còn lại: `docs/archive/pre-spec-2026-07-26/raw_research.md` §Caveats.
