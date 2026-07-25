# Scriptorium (elix/scriptorium) — Tổng hợp định hướng và nghiên cứu

> Tài liệu tổng hợp toàn bộ quá trình thảo luận và kết quả nghiên cứu sâu, phục vụ làm tài liệu tham chiếu nội bộ cho quyết định pivot từ EduStation sang Scriptorium.
>
> Ngày tổng hợp: 26/7/2026

---

## PHẦN A — TỔNG HỢP ĐỊNH HƯỚNG (từ thảo luận)

### A.1 Xuất phát điểm: bài học từ EduStation

EduStation là app agentic kiểu "Claude Code cho giáo viên Việt Nam" — desktop app riêng cho K-12 với harness Tauri/Python tự xây, workspace sandbox, audit chain theo từng tool call, planning-phase HITL, và định dạng skill pack riêng (`SKILL.md` v3, 16 field frontmatter).

**Đánh giá lại**: không phải "thất bại" theo nghĩa kỹ thuật — M1-M3 (engine, agentic loop, tool dispatcher) đã "substantially landed", một SKKN thật đã được tạo và review qua Gemini. Vấn đề nằm ở **governance-trước-traction**: đầu tư rất sâu vào một vertical duy nhất (18 R-rules, 5 non-negotiables, corpus pháp lý VN vendored đầy đủ) trước khi M4 (marketplace + pilot với người dùng thật) được bắt đầu.

**Tài sản thật sự giữ lại được** (domain-agnostic, không gắn với giáo dục):
- Agentic loop, workspace sandbox, tool dispatcher
- Định dạng skill pack + planning-phase HITL làm gate duy nhất
- Audit chain, risk-tiering (N1–N5 data sensitivity)
- 18 R-rules (đặc biệt R18: token budget cap per session — phòng runaway cost)

### A.2 Quyết định pivot: từ "xây app/harness" sang "skill-first"

**Luận điểm cốt lõi**: lớp harness/CLI agent đang bị hàng hóa hóa nhanh. Bằng chứng hội tụ:
- Kimi Code CLI (Moonshot, MIT), Grok Build (xAI, Apache 2.0), Gemini CLI (Google, Apache 2.0 code) đều đã mở, đều hỗ trợ Agent Skills, MCP, subagents, hooks.
- Grok Build công khai port code từ `openai/codex` và `sst/opencode` — chính các hãng lớn cũng không viết harness từ đầu nữa.
- SKILL.md / Agent Skills đã trở thành **chuẩn mở cross-vendor thật** (Anthropic công bố 18/12/2025 tại agentskills.io), không phải một tính năng riêng của một sản phẩm.

**Hệ quả chiến lược**: giá trị không còn nằm ở việc tự xây harness, mà nằm ở lớp **chất lượng và an toàn của skill** — điều mà cả ngành thừa nhận là chưa giải quyết xong (xem Phần B).

**Quyết định**: Phase 1 = xây hệ thống tạo/kiểm thử/audit/quản lý skill (Scriptorium), KHÔNG xây app/CLI/harness riêng. Vỏ (shell) để sau — thậm chí có thể không bao giờ cần tự xây, vì skill đã chạy được trên hệ sinh thái ~44 platform sẵn có. Mô hình kinh doanh có thể là trở thành lớp nội dung/chất lượng tốt nhất, phân phối qua hệ sinh thái đó.

### A.3 Về hạ tầng AI backend (Elixverse)

- Elixverse API là OpenAI-compatible (`chat/completions`, `images`, `embeddings`, `audio/speech`, Bearer key `elix_sk_...`), nên adapter sang Kimi Code CLI hay bất kỳ harness OpenAI-compatible nào là việc cấu hình `base_url`, không phải viết lại.
- **Gap cần platform nâng cấp trước khi dùng cho agent loop tự động**: hiện tại API key **không có spend cap hay scope riêng** — có toàn quyền như tài khoản gốc. Đây là rủi ro thật (đối chiếu chính bài học R18 của EduStation, và sự cố Railway 4/2026 — agent xóa production DB trong 9 giây vì token không bị giới hạn phạm vi). Cần: per-key spend cap, scoped keys, short-lived token, tool-calling/streaming đủ trưởng thành cho vòng lặp agent dài.

### A.4 Tên repo

Quyết định cuối: **`elix/scriptorium`** (thay vì `praxis_skills`, vì `praxis` đã là định danh riêng cho hệ thống giáo dục lập trình của Elixverse). "Scriptorium" — tu viện chuyên chép tay và chuẩn hóa văn bản thời trung cổ — khớp tinh thần "skill được viết chuẩn, đúng, đỉnh cao".

### A.5 Kiến trúc hệ thống: bộ skill lõi (bootstrap set)

Thứ tự pipeline đề xuất:

1. **Research / thu thập thông tin** — web search, source grounding. Làm trước tiên vì mọi bước sau phụ thuộc vào nó.
2. **Elicit tacit process** — phỏng vấn/đọc tài liệu chuyên gia thật, chuyển tri thức ngầm thành quy trình có cấu trúc. Đây là input chất lượng cao duy nhất cho bước 3 (xem Phần B.7 — self-generated skill không có ích gì nếu thiếu bước này).
3. **Skill_creator (tổng quát hóa)** — nhận input từ (1)+(2), sinh `SKILL.md` theo đúng **spec mở agentskills.io** (6 field: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`), không dùng manifest riêng của EduStation, để tối đa hóa portability thật.
4. **Quality evaluation loop** — chấm chất lượng qua tác vụ thật, chạy chéo trên ít nhất 2 harness đã xác nhận trong showcase chính thức (vd. Claude Code + Codex CLI) để kiểm tra portability thật.
5. **Security / injection audit** — bước riêng biệt, KHÔNG gộp với bước 4. Đa lớp: static scan + LLM semantic + runtime check, đối chiếu OWASP Agentic Skills Top 10.
6. **Skill scout/harvester** — tìm và phân tích sâu skill/repo có sẵn trong hệ sinh thái ngoài (GitHub, marketplace), chuyển đổi thành định dạng nội bộ.
7. **License-compliance check** — bắt buộc, ngay sau bước 6, trước khi vào bước 3: phân loại MIT/Apache (an toàn, cần attribution) vs GPL (copyleft, ràng buộc nếu phân phối) vs paid-marketplace (ToU hạn chế redistribute).
8. **Dedup / novelty-check** — tra registry trước khi tạo skill mới, tránh làm lại thứ đã có.
9. **Registry đa trục** — xương sống định danh, dùng tag (không category cứng), tối thiểu 4 trục: domain/nghề, loại tác vụ (research/chuyển đổi tài liệu/soạn thảo/rà soát/điều phối), risk-tier (kế thừa tinh thần N1–N5 của EduStation, tái áp dụng thành mức rủi ro đầu ra), harness-compatibility (đã verify chạy sạch trên harness nào).

### A.6 Vertical thử nghiệm đầu tiên: pháp lý Việt Nam

Cụm skill dự kiến: tra luật, chuyển văn bản luật → markdown, soạn văn bản/công văn, duyệt luật, tạo hợp đồng — phân theo risk-tier (tra luật/chuyển đổi = rủi ro thấp; tạo hợp đồng/duyệt luật = rủi ro cao, bắt buộc HITL gate).

**Cập nhật quan trọng từ nghiên cứu**: thị trường AI pháp lý VN đã đông (aitracuuluat.vn, AI Luật của LuatVietnam, LEXcentra, CLS của CMC, Trợ Lý Luật, EmLaw) — nên Scriptorium **không cạnh tranh ở lớp chatbot tra luật**, mà định vị ở lớp meta: sản xuất + kiểm định + audit skill pháp lý portable, chạy được trên nhiều harness, có citation-grounding và versioning văn bản luật — thứ mà các app đóng hiện tại không cung cấp.

### A.7 Nguyên tắc xuyên suốt đã thống nhất

- Giữ **nguyên lý** từ EduStation (risk-tiered gating, audit trail, planning-phase HITL, injection-safety bắt buộc), bỏ **cụ thể hóa** riêng cho một harness/vertical (manifest 16-field, N1-N5 gắn cứng dữ liệu học sinh).
- Nhắm thẳng vào spec mở của ngành (agentskills.io) thay vì tự phát minh định dạng riêng.
- Không tự động hóa hoàn toàn khâu tạo skill — bắt buộc có con người curate ở bước elicit-process, vì dữ liệu benchmark cho thấy skill tự sinh không có ích lợi trung bình.

---

## PHẦN B — TOÀN VĂN BÁO CÁO NGHIÊN CỨU SÂU

### TL;DR

- **Hướng đi "skill-first" của Scriptorium là ĐÚNG và được củng cố mạnh bởi dữ liệu nửa đầu 2026**: lớp harness/CLI đang bị hàng-hóa-hóa nhanh (Grok Build của xAI port code từ openai/codex và sst/opencode; Google khai tử Gemini CLI đẩy sang Antigravity CLI đóng-nguồn), trong khi chất lượng và bảo mật skill vẫn là bài toán chưa giải — SkillsBench chứng minh curated skills tăng pass rate **+16.2pp** còn self-generated skills "no benefit on average", và Snyk tìm thấy **36.82%** skill có lỗ hổng bảo mật.
- **Cần sửa vài con số/giả định cụ thể**: "chất lượng trung bình 6.2/12" không khớp benchmark chuẩn nào tìm được (benchmark thực là SkillsBench — arXiv 2602.12670, và SkillBench của Arcade.dev); "~140,000 issues / ~22,500 skills" khớp một phần với corpus SkillRet (22,795 skills) nhưng con số issue cần kiểm lại; adoption không phải "20-40+" mà hiện **~44 nền tảng** theo showcase chính thức của agentskills.io.
- **Vertical pháp lý Việt Nam đã đông đúc** (aitracuuluat.vn, AI Luật của LuatVietnam, LEXcentra, CLS của CMC, Trợ Lý Luật, EmLaw...) — nên Scriptorium KHÔNG cạnh tranh trực tiếp ở lớp "chatbot tra luật" mà định vị ở lớp meta: sản xuất, kiểm định chất lượng và audit bảo mật skill pháp lý *portable*, với citation-grounding và human-gating bắt buộc cho contract drafting.

### Key Findings

#### 1. Trạng thái hệ sinh thái Agent Skills / SKILL.md (cập nhật mới nhất)

- **Chuẩn mở đã được xác nhận**: Anthropic phát hành Agent Skills như một open standard vào **18/12/2025**, spec đặt tại agentskills.io. Đây là chuẩn cross-vendor thật, không phải marketing.
- **Adoption breadth — SỬA con số**: Background nói "~20-40+ platforms". Showcase chính thức của agentskills.io hiện liệt kê **~44 nền tảng adopter** (mid-2026), gồm Claude Code, OpenAI Codex, Cursor, Gemini CLI, GitHub Copilot, VS Code, Goose (Block), OpenCode, OpenHands, Amp (Sourcegraph), Junie (JetBrains), Kiro (AWS), Databricks, Snowflake, TRAE (ByteDance), Mistral AI, Spring AI, Roo Code, Factory, Tabnine, v.v. Các nguồn thứ cấp cho con số dao động theo thời điểm: 26+ (đầu 2026) → 32 (tháng 3) → ~40-44 (giữa 2026).
- **CẢNH BÁO về giả định adoption cụ thể**: Kimi Code CLI, Windsurf và Zed **KHÔNG xuất hiện** trong showcase chính thức của agentskills.io (mặc dù Kimi Code CLI có hệ thống skill/plugin riêng và nhiều nguồn thứ cấp nói SKILL.md chạy trên nhiều agent). Với mục tiêu "verified portability" của Scriptorium, đây chính xác là lý do cần test thực tế trên từng harness thay vì tin danh sách tương thích do vendor/blog công bố.
- **Spec fields (quan trọng cho skill_creator)**: Spec chính thức định nghĩa 6 field trong YAML frontmatter: `name` (bắt buộc, ≤64 ký tự, phải khớp tên thư mục cha, chỉ chữ thường/số/hyphen), `description` (bắt buộc, ≤1024 ký tự), `license` (tùy chọn), `compatibility` (tùy chọn, ≤500 ký tự), `metadata` (tùy chọn, map key-value), và `allowed-tools` (tùy chọn, **đánh dấu "Experimental"**, dạng chuỗi space-separated). Khuyến nghị: SKILL.md < 500 dòng; phần instructions < 5000 tokens; progressive disclosure 3 tầng (~100 tokens metadata tại startup).
- **Quyết định bỏ 16-field manifest của EduStation là ĐÚNG**: Spec mở chỉ có 6 field và cố tình "tiny/under-specified" (Simon Willison mô tả là "a deliciously tiny specification"). Dùng đúng spec mở tối đa hóa portability — đây là lựa chọn chiến lược chính xác. Nếu cần field riêng, đặt trong `metadata` (đúng chuẩn) thay vì mở rộng frontmatter — vì các implementation khác nhau xử lý field ngoài chuẩn không đồng nhất.
- **Governance**: Có **Agentic AI Foundation (AAIF)** dưới Linux Foundation, công bố 9/12/2025, đồng sáng lập bởi Anthropic, OpenAI, Block; hơn 140-150 thành viên đầu 2026. **LƯU Ý xung đột nguồn**: AAIF xác nhận quản lý MCP, AGENTS.md và goose; việc SKILL.md có được chính thức chuyển giao cho AAIF hay không thì các nguồn thứ cấp khẳng định nhưng nguồn gốc (agentskills.io, thông báo AAIF) không nói rõ. Coi đây là "khả năng cao nhưng chưa xác nhận".
- **Không có version number chính thức** (không "v1.0/v1.1") — spec được duy trì dạng living docs trong repo agentskills/agentskills (code Apache 2.0, docs CC-BY-4.0).
- **Guidance chính thức của Anthropic**: Bài engineering blog "Equipping agents for the real world with Agent Skills" (Barry Zhang, Keith Lazuka, Mahesh Murag) + "Skill authoring best practices" trên platform.claude.com + PDF "The Complete Guide to Building Skills for Claude". Anthropic có sẵn `skill-creator` skill (built-in Claude.ai và Claude Code) — có thể tham chiếu làm baseline cho skill_creator của Scriptorium.

#### 2. Chuẩn cạnh tranh / bổ trợ

Không phải cạnh tranh mà là các tầng bổ trợ: MCP (tầng truy cập tool/data — "plumbing", ~97M downloads/tháng, 10,000+ MCP server đầu 2026), SKILL.md (tầng tri thức thủ tục — "brain"), AGENTS.md (tầng cấu hình project — do OpenAI phát hành tháng 8/2025, được **"hơn 60,000 open source projects"** áp dụng theo thông báo AAIF của Linux Foundation ngày 9/12/2025, gồm Amp, Codex, Cursor, Devin, Factory, Gemini CLI, GitHub Copilot, Jules, VS Code), A2A (giao tiếp multi-agent). Litmus test của Anthropic: "Skill giải thích CÁCH theo một quy trình; MCP là thứ agent với tới khi cần database/file chưa có". Scriptorium nên tận dụng cả 3 tầng, không coi chúng là đối thủ.

#### 3. Quality evaluation & security auditing — cơ sở xây pipeline QA

- **SkillsBench TỒN TẠI (xác nhận)** — arXiv 2602.12670, repo benchflow-ai/skillsbench. Phương pháp: 86-87 tasks / 11 domains, deterministic verifiers, chạy 3 điều kiện (no-Skills / curated-Skills / self-generated-Skills), 7 agent-model configs, 7,308 trajectories. **Kết quả chính**:
  - Curated skills nâng pass rate trung bình **+16.2pp** (khớp con số "~16 điểm phần trăm" đã dùng trước đó — XÁC NHẬN).
  - Hiệu ứng RẤT không đồng đều: +4.5pp (Software Engineering) đến +51.9pp (Healthcare); 16/84 task cho delta ÂM.
  - **Self-generated skills "provide no benefit on average"** — model KHÔNG tự viết được tri thức thủ tục mà nó hưởng lợi khi tiêu thụ.
  - Focused skills 2-3 module vượt trội bundle lớn/exhaustive; model nhỏ + skills có thể sánh model lớn không skills.
- **SỬA con số "6.2/12"**: Đây có vẻ là nhầm với SkillBench của **Arcade.dev** (chấm ~39,014 skills theo 6 chiều, thang điểm khác, không phải "6.2/12"). Arcade.dev SkillBench báo **73% skill mang "elevated safety risk"**, 7,034 skill bị "hard safety gate" và quarantine. Không tìm thấy benchmark chuẩn nào cho điểm "6.2/12" — nên coi con số này là chưa xác thực và bỏ khỏi tài liệu.
- **Security auditing — con số XÁC NHẬN và bổ sung**:
  - Snyk "ToxicSkills" (scan 3,984 skills từ ClawHub + skills.sh, 5/2/2026): **36.82% (1,467 skill) có ít nhất 1 lỗ hổng**; 13.4% (534 skill) có lỗi critical; 76 malicious payload xác nhận (credential theft, backdoor, exfiltration). Snyk báo cáo **91% verified malware kết hợp language jailbreaks + executable payloads**; công cụ mcp-scan của Snyk đạt "90-100% recall trên malicious skill đã xác nhận, 0% false positive trên top-100 skill hợp pháp".
  - Snyk "Leaky Skills": 283 skill (7.1% ClawHub) rò rỉ credential plaintext qua context window/logs.
  - **CẢNH BÁO quan trọng cho Scriptorium**: Snyk công bố "Why Your Skill Scanner Is Just False Security" — pattern-matching scanner BỎ SÓT phần lớn threat nghiêm trọng vì chúng dựa vào thao túng chỉ dẫn ngôn ngữ tự nhiên, không phải chữ ký code. Attacker sau đó chuyển sang SKILL.md "sạch" redirect qua trang cài đặt giả (ClawHavoc / "clawdhub" campaign, VirusTotal phát hiện hàng trăm skill độc). Điều này xác nhận thiết kế của Scriptorium (tách security thành pipeline stage riêng) là đúng, nhưng phải kết hợp static + LLM semantic + runtime, không chỉ regex.
  - **Con số "~140,000 issues / ~22,500 skills"**: Corpus 22,795 skills khớp với **SkillRet benchmark** (arXiv 2605.05726, crawl từ claude-plugins.dev, lọc còn 17,810). Con số "140,000 issues" không tìm thấy nguồn trực tiếp — cần kiểm lại; có thể là tổng hợp từ một audit khác.
  - **Công cụ/khung tham khảo**: skill-audit (pors/skill-audit — prompt injection + trufflehog/gitleaks + shellcheck + semgrep, output SARIF); Snyk mcp-scan; VirusTotal (đã tích hợp scan ClawHub bằng Gemini 3 Flash); Bitdefender AI Skills Checker; Silverfort ClawNet. Benchmark học thuật: SKILL-INJECT (arXiv 2602.20156), SkillGuard (permission framework, arXiv 2606.03024), STARS (skill-triggered audit, arXiv 2604.10286), SkillScan/SkillProbe/SkillSieve, SkillAttack (automated red teaming, arXiv 2604.04989), "Agent Skills Enable a New Class of... Prompt Injections" (arXiv 2510.26328). **OWASP có project "Agentic Skills Top 10"** — nên dùng làm khung chuẩn cho security stage.
  - **8-point checklist của Agensi (XÁC NHẬN)**: prompt injection, data exfiltration, secret detection, dangerous commands, obfuscation, external fetches, credential access, privilege escalation. Đây là template tốt để khởi tạo security stage của Scriptorium.

#### 4. Taxonomy & registry design — kiểm chứng con số

- **SkillsMP — SỬA/CẬP NHẬT con số**:
  - Nguồn productmarketfit.tech (đầu 2026) xác nhận "1.6M+ skills, 23 occupation groups, 867 job categories".
  - Nhưng trang chủ SkillsMP hiện hiển thị **2,330,640 skills** (đã tăng lên ~2.3M) — con số 1.6M đã CŨ.
  - Taxonomy SkillsMP dựa trên **SOC (Standard Occupational Classification) của US Dept of Labor** cho trục occupation, cộng ~12 category theo use-case (Development, Business, Data & AI, DevOps, Testing & Security...). Đáng chú ý cho Scriptorium: SkillsMP ghi rõ "một skill có thể thuộc nhiều category" — xác nhận triết lý tagging đa trục (không single-category cứng) là đúng hướng ngành. (Đáng chú ý có category "Real Estate & Legal" ~40,831 skills.)
- **Skills.sh — SỬA con số**:
  - Skills.sh do **Vercel** vận hành, ra mắt 20/1/2026, mô hình leaderboard theo install telemetry (All Time / Trending 24h / Hot), cài bằng `npx skills add owner/repo`, hỗ trợ 19-20+ agent.
  - Con số listing: **~669,670 skills (6/2026)** theo rywalker.com — GẦN với "600k" nhưng đã cao hơn; top skill (vercel-labs find-skills) đạt 2.0M installs, Anthropic frontend-design 531.8K installs. Một nguồn khác nói "90,000+ skills" (có thể đếm package vs skill khác nhau). Coi ~670k là con số listing đáng tin nhất giữa 2026.
- **Các directory khác**: Agensi (curated + security-scanned + creator payment 70%, ~1,600 skills), ClaudeSkills.info (658+ free), LobeHub (169K+), NanoSkill.ai (**hand-reviewed, vertical marketing** — SEO/ads/email/lead gen, mô hình "đối lập với scrape GitHub").
- **Bài học cho registry Scriptorium**: Mô hình đa trục của Scriptorium (domain/occupation × task-type × risk-tier × harness-compatibility) là ĐÚNG và tiên tiến hơn hầu hết marketplace hiện có (đa số chỉ có 1-2 trục: occupation HOẶC category). Trục **harness-compatibility (verified)** là điểm khác biệt thực sự — không marketplace lớn nào hiện làm verified cross-harness. Trục **risk-tier** (kế thừa N1-N5 của EduStation, tái áp dụng thành output-risk/liability tier) rất phù hợp với hướng pháp lý.

#### 5. Trạng thái các open-source agent CLI (xác nhận/sửa)

- **Kimi Code CLI (Moonshot AI) — XÁC NHẬN + cập nhật**: MIT license (repo code), viết bằng TypeScript, kế thừa kimi-cli cũ, phân phối qua npm/script, lệnh `kimi`. Có subagents (coder/explore/plan), MCP qua `/mcp-config`, hooks, plugin marketplace hiển thị "trust level" khi cài. **Cấu hình custom provider (OpenAI-compatible) VẪN được hỗ trợ** — có thể trỏ sang Anthropic, OpenAI, Google hoặc provider khác bằng cách sửa config. Model chạy nền: Kimi K2.5 → K2.7-Code (12/6/2026) → **Kimi K3 (16/7/2026, 2.8T params MoE, context ~1.05M tokens)**. Weights dưới **Modified MIT** (attribution chỉ khi >100M MAU hoặc >$20M doanh thu/tháng). **LƯU Ý**: Không xác nhận được chi tiết "skill-loading brand-priority merge behavior" từ nguồn công khai — cần test thực tế.
- **Grok Build (xAI) — XÁC NHẬN + tin quan trọng**: Open-source **16/7/2026** dưới **Apache 2.0**, viết bằng Rust (~1M dòng), là "source-transparency release, KHÔNG nhận external PR", issues bị tắt, security qua HackerOne. **Tình tiết nghiêm trọng**: Ngay trước khi open-source, researcher (handle Cereblab, dùng mitmproxy) phát hiện Grok Build CLI v0.2.93 **âm thầm upload toàn bộ repo — gồm SSH keys, password database — lên Google Cloud bucket của xAI**; Musk tuyên bố xóa toàn bộ data đã upload và disable tính năng. xAI open-source 3 ngày sau, một phần để khôi phục niềm tin. Grok Build **port tool implementations từ openai/codex và sst/opencode** (theo THIRD-PARTY-NOTICES, tuân Apache §4(b)). → Đây là bằng chứng MẠNH nhất cho luận điểm "harness đang commoditized" của Scriptorium, và cũng là ca-học điển hình về rủi ro exfiltration của harness đóng.
- **Gemini CLI → Antigravity CLI — XÁC NHẬN**: Google công bố tại I/O (19/5/2026); Gemini CLI ngừng phục vụ Google AI Pro/Ultra/free tier từ **18/6/2026**; Antigravity CLI viết bằng Go, closed-source, binary `agy`, giữ Agent Skills/Hooks/Subagents/Extensions(→Plugins). Gemini CLI vẫn dùng được với **paid API key** (Apache 2.0 code không đổi, vẫn fork được). Free tier 1,000 req/ngày biến mất; Antigravity free tier bị report chỉ ~20 req/ngày. Cộng đồng phản ứng mạnh. → Củng cố luận điểm harness không đáng để tự xây và KHÔNG nên phụ thuộc backend miễn phí của vendor.
- **Bổ sung landscape**: OpenAI Codex CLI (Apache 2.0) — báo cáo **vượt 5 triệu weekly active users tính đến 2/6/2026** (tăng từ ~600,000 đầu năm) — hỗ trợ SKILL.md từ 12/2025 qua `~/.codex/skills/`. Ngoài ra: OpenCode/opencode (community-governed), Aider (fully open-source, BYO key), LangChain deepagents-CLI (tích hợp Agent Skills từ 11/2025), Nous Research Hermes Agent. Nhiều harness = càng chứng minh lớp harness đang bị hàng hóa hóa.

#### 6. Vertical pháp lý Việt Nam — landscape cạnh tranh

- **Thị trường ĐÃ ĐÔNG**: aitracuuluat.vn (Decom Stars + Viện ABAII, 350,000+ văn bản, tuyên bố 90% chính xác, 50,000+ user, ~1 triệu lượt tra cứu), AI Luật của LuatVietnam (văn bản từ 1945, đa ngôn ngữ), **LEXcentra** (legal research + contract review + contract drafting theo luật VN, hạ tầng AWS), **CLS của CMC** (460,000+ văn bản, tự động đối chiếu chồng chéo/mâu thuẫn quy định), Trợ Lý Luật (dẫn nguồn pháp lý, công cụ tính thuế/BHXH), EmLaw (tra cứu + hỏi đáp + soạn hợp đồng tự động).
- **Hàm ý chiến lược**: Các flagship skill dự kiến (tra luật, chuyển statute → markdown, soạn công văn, review văn bản, soạn hợp đồng) ĐỀU đã có sản phẩm cạnh tranh ở lớp end-user. Scriptorium nên định vị ở **lớp meta/portable skill** (sản xuất + QA + audit + registry skill pháp lý chạy được trên nhiều harness) thay vì làm thêm một "chatbot tra luật" nữa. Lợi thế: các đối thủ là app đóng, không portable; skill pháp lý portable + được audit là khoảng trống thật.
- **Best practices pháp lý AI (chuyển giao từ thị trường khác)**:
  - Hallucination citation là rủi ro số 1: nghiên cứu **Stanford RegLab/HAI "Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools"** (Magesh et al., *Journal of Empirical Legal Studies* 2025; arXiv 2405.20362) kết luận Lexis+ AI hallucinate ~17%, Westlaw AI-Assisted Research ~33%, GPT-4 ~43%, trên 202 truy vấn preregistered. LLM tổng quát fabricate citation 30-45%.
  - Tiền lệ kinh điển: **Mata v. Avianca, Inc., 678 F. Supp. 3d 443 (S.D.N.Y. 2023)** — 22/6/2023 Thẩm phán P. Kevin Castel phạt $5,000 theo Rule 11 với luật sư Steven Schwartz và Peter LoDuca vì 6 vụ án bịa do ChatGPT sinh ("bogus judicial decisions with bogus quotes and bogus internal citations").
  - **Bốn dạng hallucination pháp lý**: (1) citation statute bịa, (2) trích quy định đã bị bãi bỏ (outdated norms — LIÊN QUAN TRỰC TIẾP tới yêu cầu versioning khi luật thay đổi), (3) nhầm lẫn thẩm quyền/jurisdiction, (4) lập luận sai logic.
  - **Kỹ thuật grounding**: RAG bắt buộc + citation-grounding metric (arXiv 2606.00898) + HalluGraph (knowledge-graph alignment, arXiv 2512.01659) — verify entity + relation preservation trước khi trả lời, dưới ngưỡng thì re-retrieve hoặc chuyển human review. Citation phải hyperlink về đúng đoạn văn bản gốc.
  - **Human-in-the-loop gate**: Nghĩa vụ giám sát nằm ở cuối quy trình drafting; contract drafting rủi ro thấp hơn research nhưng vẫn có (chèn điều khoản không đúng jurisdiction, điều khoản không thể thi hành). → Xác nhận thiết kế của Scriptorium: risk-tier cao (contract drafting) BẮT BUỘC human gate.

#### 7. Critiques & lessons-learned về "skill-first"/meta-skill

- **Rủi ro lớn nhất — được chứng minh bằng benchmark**: SkillsBench chứng minh **self-generated skills "no benefit on average"**. Đây là cảnh báo TRỰC TIẾP cho meta-skill skill_creator của Scriptorium: nếu để agent tự sinh skill mà không có human curation/review, chất lượng có thể không cải thiện, thậm chí âm. → Bootstrap set của Scriptorium PHẢI có human-in-the-loop trong quality loop, không chỉ tự động hóa hoàn toàn.
- **Elicit tacit process là hướng đúng**: Nghiên cứu (SkillForge arXiv 2604.08618, SkillNet arXiv 2603.04448) chỉ ra "generic skill creators lack domain grounding, producing poorly aligned initial skills" — chính xác là vấn đề mà meta-skill "elicit tacit process" của Scriptorium nhắm giải quyết. Trích xuất quy trình từ chuyên gia thật (human-curated) là cách duy nhất đạt được mức gain của "curated skills".
- **Self-evolution có triển vọng nhưng cần feedback loop**: SkillForge cho thấy self-evolution loop dựa trên deployment feedback đạt +9-12pp Strict CR qua 3 vòng — nhưng cần cơ chế trace failure về skill deficiency. Các hệ tương tự: SkillComposer (arXiv 2606.06079), SkillOS (RL-trained curation, arXiv 2605.06614), AgentSkillOS, PolySkill, Voyager (skill acquisition trong Minecraft — tiền lệ sớm nhất).
- **Security review skill bỏ sót tấn công tinh vi**: Đã nêu ở mục 3 — pattern-matching bỏ sót; attacker chuyển sang SKILL.md "sạch" redirect qua trang cài đặt giả. → Security stage của Scriptorium không được dựa vào một lớp scan duy nhất.

#### 8. Hạ tầng Elixverse API — best practices về spend cap & tool-calling

- **Rủi ro "API key không có spend cap/scope" là NGHIÊM TRỌNG và được ngành xác nhận**: Best practice hiện đại yêu cầu **per-key/per-developer/per-team budget + rate limit ở tầng gateway TRƯỚC khi cấp quyền**, scoped API keys (giới hạn model/provider/environment), phân cấp org→team→developer, tag mọi request để attribution. Sự cố tháng 4/2026: một AI coding agent xóa production database của Railway trong 9 giây vì tìm thấy long-lived token có account-scoped permission, không có environment isolation.
- **Hướng nâng cấp cho Elixverse**: (1) per-key spend cap + rate limit; (2) scoped keys (chỉ chat/completions? chỉ model X? chỉ đọc?); (3) short-lived tokens thay vì long-lived; (4) OAuth 2.0 / Rich Authorization Requests (RAR) cho fine-grained; (5) guardrails (PII detection, prompt injection filter, output validation) ở tầng gateway; (6) immutable audit logs; (7) egress control cho outbound traffic. Vì agent loop autonomous nhiều bước, một prompt injection + key toàn quyền = thảm họa (giống ca Railway và ca Grok Build exfiltration).

### Details

**Vì sao luận điểm "harness commoditizing" vững chắc**: Bằng chứng hội tụ từ nhiều hướng trong nửa đầu 2026: (a) Grok Build của xAI công khai port code editing/search từ openai/codex và sst/opencode — chính các labs đang hội tụ về cùng một format terminal agent; (b) mọi harness lớn (Claude Code, Codex CLI, Grok Build, Kimi Code, Antigravity) đều đã hỗ trợ chung Agent Skills + MCP + subagents + hooks; (c) Kimi Code CLI, Grok Build, Codex CLI, Aider, OpenCode đều open/source-available. Khi lớp harness hội tụ và mở, giá trị dịch chuyển lên lớp tri thức (skills) và lớp kiểm định — đúng chỗ Scriptorium định vị.

**Thiết kế pipeline QA/Security đề xuất**: Scout/Harvest → License-compliance check → Dedup/novelty → skill_creator (từ elicited process + research, human-curated) → Quality eval (chạy thật trên ≥2 harness) → Security audit (stage riêng, đa lớp) → Registry (đa trục). Security phải gồm: static (skill-audit/semgrep/trufflehog/shellcheck), LLM semantic classification, runtime behavior check, và đối chiếu OWASP Agentic Skills Top 10. Đừng gộp security vào quality — Snyk chứng minh scanner đơn lớp là "false security".

**Licensing — cân nhắc cho Scout/Harvester**: Đa số skill repo dùng MIT/Apache 2.0 (permissive — tái sử dụng/redistribute tự do, chỉ cần attribution + giữ notice; Apache §4(b) yêu cầu change notice như Grok Build đã làm). Nhưng có repo GPL-3.0 (copyleft — nếu tích hợp vào sản phẩm phân phối, nghĩa vụ mở nguồn lan tỏa) như erpclaw. Documentation thường CC-BY-4.0. Paid-marketplace (Agensi) có ToU hạn chế redistribute. Chưa tìm thấy dispute/takedown lớn riêng cho scraping/cloning skill. ClawHub cho phép publish chỉ với tài khoản GitHub 1 tuần tuổi → rủi ro chất lượng/độc hại cao. SkillsMP/skills.sh scrape công khai GitHub với filter ≥2 stars. → License-compliance check của Scriptorium là thiết kế đúng và cần thiết.

### Recommendations

**Giai đoạn 0 (ngay lập tức — sửa giả định & chốt spec):**
1. Cập nhật mọi tài liệu nội bộ: adoption ~44 nền tảng (không phải 20-40+); SkillsMP ~2.3M skills (không 1.6M); Skills.sh ~670k listings; bỏ con số "6.2/12" (không có nguồn) và thay bằng "73% elevated safety risk" của Arcade SkillBench + "36.82% có lỗ hổng" của Snyk; kiểm lại "140,000 issues".
2. Chốt skill_creator BÁM SÁT 6 field của spec mở (name/description/license/compatibility/metadata/allowed-tools), đặt mọi field riêng vào `metadata`. Coi `allowed-tools` là experimental.

**Giai đoạn 1 (bootstrap meta-skills — theo đúng kế hoạch, có điều chỉnh):**
3. Bắt buộc human-in-the-loop trong quality loop (vì self-generated skills "no benefit"). skill_creator phải lấy input từ "elicit tacit process" (chuyên gia thật) — đây là điều kiện để đạt +16pp của curated skills.
4. Quality eval phải chạy thật trên ≥2 harness. Ưu tiên chọn harness đã xác nhận trong showcase chính thức (Claude Code + Codex CLI hoặc Gemini/Antigravity) thay vì Kimi Code CLI (chưa xác nhận trong showcase) cho phép đo portability đáng tin — hoặc tự verify Kimi trước khi coi là target chính thức.
5. Security stage đa lớp riêng biệt, ánh xạ OWASP Agentic Skills Top 10 + 8-point checklist của Agensi; tích hợp skill-audit/semgrep/trufflehog + một lớp LLM semantic.

**Giai đoạn 2 (vertical pháp lý):**
6. KHÔNG làm chatbot tra luật (đã bão hòa). Định vị ở skill pháp lý portable + audited. Flagship nên bắt đầu ở risk-tier THẤP (tra luật, statute→markdown) trước; contract drafting (risk cao) làm sau với human-gate bắt buộc + citation-grounding (HalluGraph-style) + versioning văn bản.
7. Xây citation-grounding bắt buộc: verify entity + relation preservation về văn bản gốc; dưới ngưỡng → human review. Theo dõi outdated norms (luật bị bãi bỏ) — thiết kế versioning từ đầu.

**Giai đoạn 3 (hạ tầng):**
8. Trước khi cho agent loop autonomous chạy trên Elixverse API: triển khai per-key spend cap + scoped keys + short-lived token + gateway guardrails + audit log. Đây là điều kiện tiên quyết, không phải nice-to-have.

**Ngưỡng thay đổi quyết định:**
- Nếu một vendor (Anthropic/OpenAI) ra "skill QA/registry" chính thức có security scanning cross-harness → Scriptorium phải chuyển sang lợi thế vertical (pháp lý VN) nhanh hơn.
- Nếu SkillsMP/skills.sh thêm verified-portability + security tier → mất một phần khác biệt registry; tăng tốc trục risk-tier + vertical.
- Nếu spec agentskills.io ra version chính thức + field mới → cập nhật skill_creator ngay.

### Caveats

- **Tốc độ thay đổi cực nhanh**: Nhiều con số (số skill, adoption, model version như Kimi K3, Codex WAU) là snapshot giữa 2026 và sẽ lỗi thời nhanh.
- **Nguồn thứ cấp nhiều**: Phần lớn con số marketplace đến từ blog/marketing (agensi.io, rywalker.com, paperclipped) — directionally đúng nhưng nên coi là điểm thời gian. Con số Snyk/SkillsBench/Stanford RegLab từ nguồn gốc (arXiv, snyk.io, JELS) đáng tin hơn.
- **Chưa xác nhận**: (1) SKILL.md có chính thức thuộc AAIF không (MCP/AGENTS.md thì có); (2) con số "140,000 issues/22,500 skills"; (3) benchmark "6.2/12"; (4) chi tiết "brand-priority merge" của Kimi Code CLI; (5) Kimi/Windsurf/Zed không có trong showcase chính thức dù nguồn thứ cấp nói có.
- **Elixverse là hệ nội bộ**: Không nghiên cứu ngoài; khuyến nghị spend-cap/tool-calling là best practice chung của ngành áp cho mọi AI gateway.

### Nguồn tham khảo trọng yếu (đọc tiếp)

- **Spec & guidance**: agentskills.io/specification; anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills; platform.claude.com "Skill authoring best practices"; github.com/agentskills/agentskills.
- **Benchmark chất lượng**: SkillsBench (arXiv 2602.12670 + github.com/benchflow-ai/skillsbench); Arcade.dev SkillBench (arcade.dev/blog/skillbench-agent-skills-benchmark); SkillRet (arXiv 2605.05726); "You're probably using Agent Skills wrong" (ansonbiggs.com); O'Reilly Radar "Agent Skills Work But...".
- **Security**: Snyk ToxicSkills (snyk.io/blog/toxicskills...); Snyk Leaky Skills; OWASP Agentic Skills Top 10 (owasp.org/www-project-agentic-skills-top-10); pors/skill-audit; SKILL-INJECT (arXiv 2602.20156); SkillGuard (arXiv 2606.03024); "Agent Skills Enable a New Class of... Prompt Injections" (arXiv 2510.26328).
- **Marketplaces/registry**: skillsmp.com (+/occupations, /categories); rywalker.com/research/skills-sh; agensi.io/learn (complete list & security best practices); nanoskill.ai.
- **CLIs**: github.com/MoonshotAI/kimi-code; github.com/xai-org/grok-build + simonwillison.net/2026/Jul/15/grok-build; devops.com (Grok Build exfiltration); developers.googleblog.com (Gemini→Antigravity); thenewstack.io/google-antigravity-cli.
- **Pháp lý AI**: Stanford RegLab "Hallucination-Free?" (arXiv 2405.20362 / JELS 2025); HalluGraph (arXiv 2512.01659); Citation Grounding (arXiv 2606.00898); Mata v. Avianca 678 F. Supp. 3d 443. VN: aitracuuluat.vn, lexcentra.ai, cls.cmcai.vn, ailuat.luatvietnam.vn, trolyluat.vn, emlaw.vn.
- **API security**: curity.io/resources (8 API security best practices for AI agents); portkey.ai/blog (Codex best practices); workos.com/blog (AI agent secrets); stytch.com/blog (RAR/CIBA/DCR).
