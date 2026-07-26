# Strategy Spec — Scriptorium

| Version | Date | Author | Description |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-26 | Claude (distilled from discussion + research with owner) | First SPEC version, distilled from `docs/archive/pre-spec-2026-07-26/` (discussion transcripts + deep research report), fixed stale figures and one incorrect Elixverse description (confirmed by reading the code at `D:/elix/platform` directly). |
| 1.1.0 | 2026-07-26 | Claude | Owner confirmed: Scriptorium does not integrate any AI backend (including Elixverse) — added to §2 non-goals, rewrote §6 from "gate before use" to "not planned." |
| 1.2.0 | 2026-07-26 | Claude | Second skill: `document-ai-structurer` (Docling-based, MIT). Added principle §7 point 7: never commit venv into a skill (portability), python-env bootstrap shared once there are ≥2 Python skills. |
| 1.3.0 | 2026-07-26 | Claude | Owner requested building the 3rd infrastructure skill right away: `python-env-bootstrap` (based on `uv`), earlier than the "≥2 Python skills" threshold set in 1.2.0 — overrode the deferral, §7 point 7 updated to reflect it's built. |
| 1.4.0 | 2026-07-26 | Claude | Owner deliberately overrode the "no license-check exceptions" principle (§7 point 5, originally from `handoff.md` point 6): during the current bootstrap phase, controlled "legal debt" is allowed — see the new §7 point 5 + `registry/SCHEMA.md` field `license_debt`. |
| 1.5.0 | 2026-07-26 | Claude | Owner requested moving the venv from per-skill to a SHARED venv at the repo root — §7 point 7 updated. `python-env-bootstrap` v0.2.0 manages the shared venv, verified for real (3 Python skills installed together, no cross-import conflicts). |
| 1.6.0 | 2026-07-26 | Claude | Translated the entire document to English per owner directive (whole system except `docs/archive/` and outside-reference material must be English). |
| 1.7.0 | 2026-07-26 | Claude | 5 general-tier skills harvested from K-Dense-AI/scientific-agent-skills (`citation-management`, `literature-review`, `exploratory-data-analysis`, `hypothesis-generation`, `peer-review`). Rewrote §5 into an explicit two-stage expansion model: an **audience-tier ladder** (education vertical — Student → Teacher → University Student → Lecturer/Researcher) precedes **specializer networks** (industry-specific, Legal is first) per owner's explicit sequencing (`outside_research/`, this session). Added `outside_research/` as a recognized living-input directory (see `docs/MASTER_CONTEXT.md` §3-4). |
| 1.8.0 | 2026-07-26 | Claude | Owner clarified `outside_research/` counts as elicited input (principle 4, §7) — Claude proceeds directly to `skill-creator` from it, no separate survey required for tiers it covers. Registry gained 2 tag axes, `grounding` (mandatory) and `object_type` (optional) — see `registry/SCHEMA.md`, adapted from `outside_research/research_01_comment_01.md` §6's multi-axis tagging suggestion (took `grounding`, dropped its redundant `workflow` axis which already overlaps `task_type`, kept `object_type` as optional rather than mandatory). First Student(K12)-tier skill built: `study-plan-builder`. |
| 1.9.0 | 2026-07-26 | Claude | Surveyed all 63 EduStation skill folders before building the Teacher tier: found heavy fragmentation (15 folders = one Nghị định 30/2020 admin-document template; 5 = one lesson-planning capability; 6 = one assessment-generation capability; 11 duplicate Scriptorium's own foundation skills). Owner directed excluding the administrative-paperwork cluster entirely — teacher-tier skills serve teaching, not bureaucratic process (§5.1 updated). First Teacher-tier skill built: `lesson-plan-builder`, grounded in EduStation's domain knowledge (CV5512/TT32-2018/TT27-2020/TT22-2021) but not its orchestration machinery, used loosely per owner's explicit "not gospel" caveat. Full consolidation survey: `docs/ROADMAP.md`. |
| 1.10.0 | 2026-07-26 | Claude | Owner directed parallel sub-agent dispatch to finish the Teacher-tier shortlist. 6 skills built via independent background agents, each reviewed and independently re-tested by the orchestrating session before integration: `assessment-builder`, `grading-and-feedback`, `competency-rubric-builder`, `classroom-materials-builder`, `grade-book-builder`, `parent-communication`. Teacher tier now 7/8 done (only `teacher_self_eval` remains, lowest priority). Full build/review process: `docs/ROADMAP.md`. |
| 1.11.0 | 2026-07-26 | Claude | Owner directed jumping to the Legal specializer network next (§5.2), ahead of University Student/Lecturer tiers. Surveyed the legal cluster, consolidated 11 raw survey items into 5 skills + 1 `translator-en-vi` extension, flagged 2 real data gaps rather than inventing data around them. Building sequentially this round per owner request. First legal skill: `contract-consistency-linter` (v0.1.0). |

---

## 1. The problem & the pivot decision

EduStation (`D:/elix/edustation`) — an agentic app, "Claude Code for Vietnamese teachers" — did not fail technically (M1-M3: engine, agentic loop, tool dispatcher had "substantially landed"). It died from **governance-before-traction**: investing too deeply into a single vertical (18 R-rules, 5 non-negotiables, a fully vendored Vietnamese legal corpus) before a real pilot with actual users (M4) ever ran.

**Core argument driving the pivot**: the harness/CLI-agent layer is being commoditized fast. Evidence (mid-2026):
- Grok Build (xAI, Apache 2.0) openly ports tool implementations from `openai/codex` and `sst/opencode` — even the big labs no longer write harnesses from scratch.
- Kimi Code CLI (MIT), Grok Build (Apache 2.0), Codex CLI (Apache 2.0), OpenCode, Aider are all open, all support Agent Skills + MCP + subagents + hooks.
- Agent Skills / `SKILL.md` is now a **real cross-vendor open standard** — Anthropic published it on 2025-12-18 at agentskills.io, with the official showcase listing **~44 adopter platforms** by mid-2026 (not "20-40+" as originally estimated).

**Decision**: Phase 1 = build the skill creation/testing/audit/management system (Scriptorium). NOT a dedicated app/CLI/harness. Value shifts up to the knowledge layer (skills) and the verification layer — exactly where the whole industry admits the problem isn't solved yet (see §3).

## 2. Scope & non-goals

**In scope**: a system for creating, quality-testing, security-auditing, and cataloging (registry) portable Agent Skills, following the agentskills.io open spec, not locked to one harness.

**Out of scope** (at least for now):
- No dedicated app/CLI/agent harness — skills run on the existing ~44-platform ecosystem.
- No "legal-lookup chatbot" in the legal vertical — the Vietnamese market is already crowded (aitracuuluat.vn, AI Luật by LuatVietnam, LEXcentra, CLS/CMC, Trợ Lý Luật, EmLaw). Scriptorium positions at the **meta layer**: producing + verifying + auditing portable legal skills.
- No letting an agent self-generate a skill without input elicited from a real source — SkillsBench (arXiv 2602.12670) measured self-generated skills as "no benefit on average," while curated skills (with human-curated input) hit +16.2pp average pass rate.
- **No integrating any AI backend/API into Scriptorium** (including Elixverse) — Scriptorium's output is a pure skill artifact (`SKILL.md` + registry entry). Whichever agent runs that skill uses its own model/backend; Scriptorium never sits in the middle as an LLM-calling service for anyone. Decision made 2026-07-26 (owner, historical record in `docs/DECISIONS_PENDING.md`).

## 3. Bootstrap pipeline (9 steps, order not negotiable)

| # | Step | Purpose | Status (2026-07-26) |
| --- | --- | --- | --- |
| 1 | Research | Information gathering, source grounding | Run once for Scriptorium itself (result: this file + archive) |
| 2 | Elicit tacit process | Extract a process from a real source (an expert or the owner) | Done for `skill-creator` (elicited from the owner via the EduStation postmortem) |
| 3 | **skill-creator** | Produces a `SKILL.md` matching the 6-field spec from inputs (1)+(2) | Exists: `skills/skill-creator/SKILL.md` |
| 4 | Quality evaluation loop | Score quality by running the real skill on ≥2 verified harnesses (each harness uses its own model/backend — Scriptorium calls no AI API, see §2) | No skill built for this step yet |
| 5 | Security / injection audit | A separate stage, multi-layer (static + LLM semantic + runtime), cross-checked against the OWASP Agentic Skills Top 10 | No skill built for this step yet |
| 6 | Skill scout/harvester | Find + deeply evaluate existing skills in the outside ecosystem | No skill built for this step yet |
| 7 | License-compliance check | Mandatory right after (6), before (3) for any harvested skill | No skill built for this step yet |
| 8 | Dedup / novelty-check | Query the registry before creating a new skill | Rule already recorded in `registry/SCHEMA.md`, not yet automated as a skill |
| 9 | Multi-axis registry | The identity backbone | `registry/SCHEMA.md` + `registry/skills.json` already exist, 1 entry (`skill-creator`) |

Do not reorder (1)→(2)→(3). A skill that hasn't cleared (4) and (5) is never "ready to use," regardless of deadline.

## 4. Registry — multi-axis taxonomy

4 mandatory axes per skill: **domain** (reference SkillsMP's occupation groups directly, don't invent a taxonomy from scratch), **task-type** (research / document-conversion / drafting / review-qa / coordination — cuts across every domain), **risk-tier** (N1-N5, inherits the spirit of EduStation's tiering but is just 1 field declared at skill-declaration time, NOT a separate enforcement engine — see the EduStation survey in `docs/archive`), **harness-compatibility** (only list harnesses actually verified to run — never inferred from a vendor showcase). Full field list: `registry/SCHEMA.md`.

## 5. Vertical expansion model: audience-tier ladder, then specializer networks

Two distinct kinds of expansion happen after the general-tier skill layer (`domain: general` skills, e.g. the 5 K-Dense-AI harvests) is in place, and they are **not the same thing**:

- **Audience-tier ladder** — general-purpose skills refined for a specific *role/capability level* a person occupies (a student, a teacher), still broadly domain-agnostic in the underlying task. Not industry-specific.
- **Specializer networks** — skills scoped to a specific *industry/profession* (Legal, eventually Medicine/Finance/...), which inherit the full stack below them (foundation → general → audience-tier where applicable).

Owner's explicit sequencing (2026-07-26, `outside_research/`): finish the audience-tier ladder for the education vertical before jumping to specializer networks. Rationale stated by the owner: a system needs "đủ tứ chi, bộ não, và kiến thức kĩ năng, như một học sinh lớp 12" (a general capability base, like a 12th-grade graduate) before specialized/professional skills ("như các chuyên ngành được học") can sit on top of it usefully.

### 5.1 Audience-tier ladder — education vertical (current focus)

Order: **Student (K12) → Teacher → University Student → Lecturer/Researcher**. Then branch into specializer networks (§5.2).

| Tier | Real elicitation source available? | Status (2026-07-26) |
| --- | --- | --- |
| Student (K12) | **Owner-confirmed as of 2026-07-26.** No independent student survey exists, but the owner explicitly confirmed `outside_research/` + direct instruction count as elicitation for this tier — Claude (acting as the skill-creator sub-agent) builds directly from it, scoped conservatively. | **In progress** — `study-plan-builder` (v0.1.0) done: deterministic study/review scheduling, deliberately avoids any subject-matter content to sidestep the "doing the student's work" risk while real per-topic elicitation is still thin. |
| Teacher | **Strong.** EduStation (`D:/elix/edustation/skills/`) is a real, previously-deployed K12-teacher system with 63 skill folders — counts as a real elicited process, same standing as any other prior-art source already surveyed this session (`D:/elix/platform`, `D:/elix/researches`). Owner's explicit caveat: use it loosely ("dựa thôi chứ không phải tham khảo hẳn, vì tôi biết nó vẫn yếu") — EduStation is known-imperfect prior art, not a spec to follow literally. A full survey (`docs/ROADMAP.md`) found heavy fragmentation: 15 folders are the same Nghị định 30/2020 admin-document template, 5 are one lesson-planning capability, 6 are one assessment-generation capability, 11 duplicate Scriptorium's own foundation skills. | **7 of 8 shortlisted skills done.** `lesson-plan-builder` + 6 more (`assessment-builder`, `grading-and-feedback`, `competency-rubric-builder`, `classroom-materials-builder`, `grade-book-builder`, `parent-communication`) — the latter 6 built via parallel sub-agents and independently re-verified by the orchestrating session. Owner directed excluding the administrative-paperwork cluster entirely — this tier serves teaching, not school bureaucracy ("đáp ứng cho giáo dục, không đáp ứng cho chính trị, thủ tục rườm rà"). Only `teacher_self_eval` remains, lowest priority. Full survey/build process: `docs/ROADMAP.md` §"Teacher-tier consolidation survey." |
| University Student | **Thin.** EduStation has `research_proposal`, `thesis_guide`, `university_exam_bank` but they read as faculty/teacher-facing more than student-facing. | Not started. Needs its own survey or stronger grounding before building. |
| Lecturer / Researcher | **Substantial, already built — just not labeled as this tier.** The 5 general-tier research skills (`literature-review`, `citation-management`, `hypothesis-generation`, `peer-review`, `exploratory-data-analysis`) plus `latex-project-bootstrap`/`office-doc-creator` were built domain-agnostic but directly serve this audience. | Core covered. Remaining gap candidates (not yet elicited): grant-proposal formatting, venue-specific manuscript formatting, thesis-structure scaffolding built on `latex-project-bootstrap`. |

**Update (2026-07-26)**: the owner clarified that `outside_research/` content — including the external-AI-brainstormed skill names in `research_01_lawer-work.md` (e.g. `learning-path-planner`, `lesson-plan-generator`, `exam-matrix-builder`, `thesis-structure-bootstrap`) — is elicited input the owner is providing directly, satisfying principle 4 (§7) for tiers it covers. Claude proceeds straight to `skill-creator` from it rather than waiting on a separate survey. Judgment on scope/safety per skill still applies (see `study-plan-builder`'s deliberately conservative scope), and the Teacher tier still additionally draws on EduStation as a second, independent elicitation source (used loosely, per the owner's caveat above).

### 5.2 First specializer network: Vietnamese legal

Started after §5.1's Teacher tier was substantially staffed (7/8), per owner's explicit direction to jump ahead of University Student/Lecturer for now. Real elicitation already collected: `outside_research/research_01_survey.md` (an 11-item real practitioner survey — recent law graduate, junior legal role) plus two AI-assisted research reports (`research_01_result_01.md`, `research_01_result_02.md`) providing competency-model/maturity-model framing and cross-jurisdiction ethics context (ABA, SRA, Vietnamese practice). This satisfies principle 4 for the legal vertical specifically — it does not extend to other industries without their own survey.

Consolidated into 5 skills + 1 extension of `translator-en-vi` (not 9-11 separate skills, same discipline as the Teacher-tier survey) — full table and 2 flagged real data gaps (no free Vietnamese legal-document API for citation verification, no real government checklist/template data for form-filling) in `docs/ROADMAP.md` §"Legal-cluster consolidation survey." Building sequentially this round (owner request), starting with `contract-consistency-linter` (v0.1.0, done) since it needed no external data.

Planned flagships, ordered by risk-tier: statute lookup + statute→markdown conversion (N1-N2, low risk, first) → drafting official letters/document review (medium) → contract drafting/law review (N4-N5, high risk, **mandatory human gate**, later).

Must ship alongside: citation-grounding (verify entity + relation preservation against the source text before answering; below threshold → re-retrieve or human review) and statute versioning (tracking outdated norms — repealed law). Basis: Stanford RegLab/HAI "Hallucination-Free?" (arXiv 2405.20362) — Lexis+ AI hallucinates ~17%, Westlaw AI-Assisted Research ~33%, GPT-4 ~43%, across 202 preregistered queries; the precedent *Mata v. Avianca, Inc.*, 678 F. Supp. 3d 443 (S.D.N.Y. 2023) — $5,000 fine under Rule 11 for 6 fabricated cases generated by ChatGPT.

## 6. Elixverse (`D:/elix/platform`) — not part of the integration plan

Owner confirmed (2026-07-26): Scriptorium has no plan to integrate any AI backend, including Elixverse (see §2). This section is kept purely for reference — if direction changes in the future and one of Scriptorium's operating skills (e.g. the quality-eval loop) genuinely needs to call an AI API itself, read this again before deciding:

- **Correcting the old description**: Elixverse is NOT an "OpenAI-compatible API" — it's a proprietary, multi-provider API (Gemini/OpenAI/Anthropic), a self-designed router with an OpenAI-style structure, not following the actual OpenAI schema. Confirmed directly from code + docs on 2026-07-26 (see memory `project-platform-elixverse-status`).
- **A real gap if ever needed**: no per-key spend cap/scope (`elix_sk_...` has full account-owner privileges). Track 2 (multi-tenancy cost isolation, per-token RPM/TPM) is deferred, pending Redis rollout. If this situation ever arises, the platform team needs to solve spend-cap + scoped keys before use in any automated agent loop.

## 7. Non-negotiable principles

1. Stick to the agentskills.io open 6-field spec (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`) — Scriptorium-specific fields always live inside `metadata`.
2. Quality evaluation and security audit are two different gates — never merge into one review pass (a single-layer pattern-matching scanner has been shown by Snyk to miss most serious attacks).
3. Never mark a skill harness-compatible based on a vendor/showcase claim — only direct verification counts.
4. Never fully automate skill creation — always elicit from a real source before `skill-creator` (self-generated skills are "no benefit on average" — SkillsBench).
5. Harvesting from an outside source always goes through license-compliance-check before touching skill-creator. **Amended 2026-07-26 (owner, deliberate override)**: during the current bootstrap phase, controlled "legal debt" is permitted — harvesting/adapting from a source with unclear or restricted license (this does NOT apply to a source with an explicit contractual clause banning redistribution, e.g. Anthropic's docx/pdf/pptx/xlsx — those stay absolutely BLOCKED, not debt-eligible), provided: (a) `registry/skills.json` records `license_debt` for that skill (source, reason, remediation plan), (b) that skill is NOT distributed/published externally while in debt, (c) the full debt ledger is reviewed before the system leaves the bootstrap phase (before Phase 2, the legal vertical). This is the owner's deliberate risk decision, not an oversight — do not unilaterally "fix it properly" in a later session without asking the owner first.
6. One skill that runs well, audits clean, and gets real use beats ten skills sitting unused in the registry.
7. Never commit a venv/binary environment into git — a venv is tied to a specific OS/architecture, breaking portability. A skill needing Python declares `requirements.txt` (or an equivalent lockfile) + runtime venv-bootstrap instructions; `.venv/` always sits in `.gitignore`. **Amended 2026-07-26 (owner)**: venv no longer lives inside each individual skill — a single SHARED venv at the repo root (`<repo_root>/.venv`, sibling to `skills/`), avoiding duplicated heavy dependencies across skills. The `python-env-bootstrap` infrastructure skill (based on `uv`) manages this shared venv — every new Python skill depends on it via the registry `dependencies` field, calling `bootstrap.ps1/.sh -Requirements <skill>/requirements.txt` to add its own dependencies into the shared venv rather than creating its own.

## 8. Sources — verified figures (don't use archive figures where they differ from here)

- Agent Skills adoption: **~44 platforms** (agentskills.io showcase, mid-2026), not "20-40+."
- SkillsMP: **~2.3M skills**, 23 occupation groups, 867 job categories (not 1.6M — that figure is stale).
- Skills.sh (Vercel): **~670k skill listings** (2026-06, rywalker.com), not "~600k."
- Dropped the "average quality 6.2/12" figure entirely — no matching standard benchmark found. Used instead: Arcade.dev SkillBench — **73% of skills carry "elevated safety risk"**; Snyk ToxicSkills — **36.82% of skills have ≥1 vulnerability**, 13.4% critical.
- SkillsBench (arXiv 2602.12670): curated skills average +16.2pp pass rate (ranging +4.5pp to +51.9pp by domain); self-generated skills "no benefit on average."
- Elixverse: corrected "OpenAI-compatible" → "proprietary, multi-provider API, OpenAI-style structure" (code verified 2026-07-26).

Full secondary sourcing and the remaining unverified figures/assumptions: `docs/archive/pre-spec-2026-07-26/raw_research.md` §Caveats.
