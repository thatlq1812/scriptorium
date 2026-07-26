# Roadmap — Scriptorium

| Version | Date | Author | Description |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-26 | Claude | First version — recorded the skill-expansion backlog the owner laid out (`important.md`); owner delegated full ordering authority. |
| 1.1.0 | 2026-07-26 | Claude | Completed backlog items 1-5 in the same session: 8 new skills (`dedup-novelty-check`, `mermaid-diagram-designer`, `translator-en-vi`, `latex-project-bootstrap`, + item-5 scouting). Recorded deep-scout results from the 2 large repos. |
| 1.2.0 | 2026-07-26 | Claude | Translated to English per owner directive (whole system except `docs/archive/` and outside-reference material). |
| 1.3.0 | 2026-07-26 | Claude | 5 general-tier skills harvested (see `docs/STATUS.md`). Rewrote "Long-term direction" into a concrete audience-tier expansion plan (education vertical: Student → Teacher → University Student → Lecturer/Researcher, then specializer networks) per owner sequencing this session (`outside_research/`). |
| 1.4.0 | 2026-07-26 | Claude | Owner clarified: `outside_research/` content counts as elicited input Claude can build directly from (Claude acts as the skill-creator sub-agent). Added `grounding`/`object_type` tag axes to `registry/SCHEMA.md`, retrofitted all 18 prior entries. Built `study-plan-builder`, first Student(K12)-tier skill, deliberately scoped to pure scheduling (no subject content) since no real student survey exists yet. Owner directed the Teacher tier next, loosely grounded in EduStation (explicitly "not gospel" — known-weak prior art, same spirit as this session's own v0.2.0 hardening round finding 17 defects in skills built earlier the same day). |
| 1.5.0 | 2026-07-26 | Claude | Surveyed all 63 EduStation skill folders before building the Teacher tier — found heavy fragmentation (15 folders = one Nghị định 30/2020 admin-document template, 5 folders = one lesson-planning capability, 6 folders = one assessment-generation capability, 11 folders duplicate Scriptorium's own foundation skills). Owner directed excluding the administrative-paperwork cluster entirely ("đáp ứng cho giáo dục, không đáp ứng cho chính trị, thủ tục rườm rà"), consolidated the rest into ~6 capability clusters. Built `lesson-plan-builder` (v0.1.0), first Teacher-tier skill — a CV 5512 structural validator grounded in EduStation's domain knowledge only, not its orchestration machinery. |
| 1.6.0 | 2026-07-26 | Claude | Owner directed dispatching parallel sub-agents to complete the remaining Teacher-tier shortlist ("nó có sẵn lõi rồi, chỉ cần chắt lọc lại, rồi bạn duyệt lại một lần"). Dispatched 6 independent background agents; each built one skill self-contained (no shared-file edits) and reported back a tested skill + ready-to-paste registry/STATUS entries. Orchestrating session independently re-verified all 6 (file existence, dangerous-pattern scan, real re-execution against bundled assets) before integrating into `registry/skills.json` (26 entries now) and `docs/STATUS.md`. Teacher tier is now substantially staffed: 7 of 8 shortlisted skills done, only `teacher_self_eval` remaining. |
| 1.7.0 | 2026-07-26 | Claude | Owner directed jumping to the Legal specializer network next (skipping University Student/Lecturer tiers for now). Surveyed the legal cluster (`outside_research/`) same as the Teacher-tier survey: 11 raw survey items consolidated into 5 skills + 1 extension of `translator-en-vi`; flagged 2 real data gaps (no free Vietnamese legal-document API for `legal-citation-checker`, no real government checklist/template data for `legal-form-filler`) rather than building around them with invented data. Building sequentially this round, not via parallel dispatch, per owner request. First legal skill built: `contract-consistency-linter` (v0.1.0). |

---

## Background

Owner supplied 4 external sources, all license-verified clean (`docs/STATUS.md` — no debt needed for these):

| Repo | Stars | License | Note |
| --- | --- | --- | --- |
| `google-gemini/gemini-cli` | 106,186 | Apache-2.0 | CLI agent, referenced for architecture patterns, not a direct skill source |
| `K-Dense-AI/scientific-agent-skills` | 31,783 | MIT | 148 real scientific skills in `skills/` |
| `VoltAgent/awesome-agent-skills` | 28,962 | MIT | A curated list linking to 1000+ other skills — used as an INDEX for further discovery, doesn't contain skills itself |
| `mermaid-js/mermaid` | 89,421 | MIT | Diagram syntax, source for `mermaid-diagram-designer` |

A "Top 10 Agent Skills repos" blog post the owner pasted had **unverifiable figures** (e.g. "Matt Pocock Skills 130k+ stars" — the real repo tops out at 59 stars; "Superpowers" has no matching repo findable on GitHub) — **not used as a source**, only direct verification via `gh api`/`gh search` counts, as done for the 4 repos above.

The image the owner sent (`1785053923858_...jpg`) is an org-chart-style diagram of 42 skills from a different commercial product (grouped by department: Dev/Design/Marketing/Social/Finance/Small-business/Legal) — used as **structural inspiration for future domain expansion**, content not copied.

## Principle applied to every new skill from now on (owner, 2026-07-26)

A skill with only a `SKILL.md` does NOT meet the bar. A quality skill needs enough supporting files (`scripts/`, `references/`, `assets/` as appropriate) that "looking it over tells you what it'll do and makes you actually want to use it" — not pure text describing intent.

## Backlog (execution order chosen by Claude)

| # | Item | Ordering rationale | Status |
| --- | --- | --- | --- |
| 1 | `dedup-novelty-check` (stage 8) | Rule already existed in `registry/SCHEMA.md`; finish staffing the pipeline skeleton (9/9 stages with an operating skill) before expanding sideways | **Done** — `skills/dedup-novelty-check/` |
| 2 | `mermaid-diagram-designer` | MIT, clear architecture (text syntax → diagram), testable immediately without a long elicit | **Done** — `skills/mermaid-diagram-designer/` |
| 3 | `translator-en-vi` | No external repo scouting needed — elicited directly from the owner on translation quality control (terminology, register), other languages later | **Done** — `skills/translator-en-vi/` |
| 4 | LaTeX/research skill(s) from `D:\elix\researches` | Needed deeper reading of the real structure (`textbooks/document_engineering/`, `docs/methodology/idea_to_book_series.md`, `elix-textbook.cls`) to elicit the actual process instead of guessing — more time than the 3 items above | **Done** — `skills/latex-project-bootstrap/` (generic scaffold, didn't copy the project-specific `.cls`) |
| 5 | Deep-scout `scientific-agent-skills` (148 skills) + browse the `awesome-agent-skills` catalog (1000+ entries) | Largest volume of work — best done after having 3-4 high-quality sample skills to calibrate against, to avoid mass-harvesting then discovering a standard mismatch that requires redoing everything | **Scouting done, harvesting not yet done** — see "Item 5 scout results" below |
| 6 (optional) | Image-generation skill (using the user's own API key) | Owner marked optional, referencing `D:/elix/platform/scripts`, `D:/UNI/S9_SP26/MLN131/project` | **Done, expanded into a designer toolkit** — `skills/image-generator-gemini/`, grounded in a full survey of both referenced projects. Verified for real via actual API calls (owner-authorized test key). |

## Item 5 scout results (2026-07-26)

**`K-Dense-AI/scientific-agent-skills`** (148 real skills in `skills/`, MIT, verified via `gh api`): broad coverage — domain-specific scientific tooling (`biopython`, `scanpy`, `rdkit`, `qiskit`, `pymatgen`...), statistical analysis (`statsmodels`, `pymc`, `scikit-survival`), scientific writing/presentation (`scientific-writing`, `scientific-slides`, `literature-review`, `peer-review`, `citation-management`), and a few skills that **overlap with what Scriptorium already has** (`docx`, `pptx`, `xlsx`, `pdf`, `markitdown`, `latex-posters` — run `dedup-novelty-check` before harvesting any of these; high odds of overlap with the existing `office-doc-creator`/`document-ai-structurer`). Candidates worth harvesting first (no overlap, high value, low narrow-domain coupling): `citation-management`, `literature-review`, `experimental-design`, `statistical-power`, `exploratory-data-analysis`.

**`VoltAgent/awesome-agent-skills`** (curated link list, MIT): structured by Official/Core/by-programming-language (.NET/Java/Python/Rust/TypeScript)/NVIDIA-tooling/Community. Has a "Skill Quality Standards" table (third-person description + specific keywords, progressive disclosure <500 lines, **no hard-coded absolute paths**, scoped tools instead of `"tools": ["*"]`) — matches most of the principles Scriptorium already set independently, confirming the direction is aligned with community standards. One thing to self-check: audit Scriptorium's existing scripts for any hard-coded absolute path (`check_dedup.py` uses `Path(__file__).resolve().parents[2]` — relative, safe; need to check the remaining scripts too).

Haven't harvested any specific skill from these two sources yet — waiting on owner priority confirmation before proceeding (see end of session).

## Long-term direction: audience-tier expansion model

General-purpose skill clusters first → skills by audience (education vertical) → specializer networks (industry). Formalized in `docs/specs/STRATEGY_SPEC.md` §5. Source: `outside_research/` (owner-authored surveys + external AI-assisted analysis, 2026-07-26) — see `docs/MASTER_CONTEXT.md` §3-4 for how that directory is treated (living input, not a source of truth on its own).

### Status of general-tier skills (done this session)

5 skills harvested from K-Dense-AI/scientific-agent-skills (MIT): `citation-management`, `literature-review`, `exploratory-data-analysis`, `hypothesis-generation`, `peer-review`. See `docs/STATUS.md`.

### Next: audience-tier ladder, education vertical

Order: **Student (K12) → Teacher → University Student → Lecturer/Researcher**, then branch into specializer networks. Full reasoning and per-tier elicitation-source status: `docs/specs/STRATEGY_SPEC.md` §5.1. Summary:

| # | Tier | Elicitation source | Status |
| --- | --- | --- | --- |
| 1 | Student (K12) | Owner confirmed `outside_research/` + direct owner instruction count as elicitation for this tier (2026-07-26) | **In progress** — `study-plan-builder` done (scheduling only, deliberately avoids subject content) |
| 2 | Teacher | Strong — EduStation (`D:/elix/edustation/skills/`, 63 folders, previously deployed), used loosely (owner: "dựa thôi chứ không phải tham khảo hẳn, vì tôi biết nó vẫn yếu" — treat as rough prior art, not gospel) | **In progress** — `lesson-plan-builder` done (see consolidation survey below) |
| 3 | University Student | Thin — EduStation's `research_proposal`/`thesis_guide`/`university_exam_bank` are faculty-facing, not student-facing | Not started; needs its own survey or stronger grounding |
| 4 | Lecturer / Researcher | Substantial — already covered by this session's 5 general-tier research skills + `latex-project-bootstrap`/`office-doc-creator`, just not labeled as an audience tier | Core covered; gap candidates: grant-proposal formatting, venue-specific manuscript formatting, thesis-structure scaffolding |

**Candidate skill names are not pre-approved for building.** `outside_research/research_01_lawer-work.md` contains an external AI's brainstormed skill list per tier (e.g. `learning-path-planner`, `concept-visualizer`, `homework-rubric-checker` for Student; `lesson-plan-generator`, `exam-matrix-builder`, `slide-deck-architect`, `student-feedback-summarizer` for Teacher; `thesis-structure-bootstrap`, `literature-matrix-builder`, `academic-paraphraser-vi` for University Student; `grant-proposal-scaffold`, `manuscript-peer-reviewer`, `journal-formatter` for Lecturer/Researcher). These are useful as a starting shortlist to survey against, not a build list — principle 4 (`docs/specs/STRATEGY_SPEC.md` §7) still requires elicitation from a real source per tier before `skill-creator` runs.

**On EduStation as a source for the Teacher tier**: EduStation counts as real elicited process (a previously-deployed system), same standing as `D:/elix/platform`/`D:/elix/researches` already surveyed this session. But its architecture baked in machinery Scriptorium deliberately does not replicate — 18 R-rules, a 5-tier enforcement engine, harness-specific dispatcher hooks (see `docs/archive/` for the full EduStation audit). Borrow the *workflow/problem shape* the same way `latex-project-bootstrap` and `image-generator-gemini` borrowed from their reference projects — read, understand, rewrite from scratch; never copy EduStation code or its governance machinery wholesale.

### Teacher-tier consolidation survey (2026-07-26)

Surveyed all 63 EduStation skill folders' `SKILL.md` frontmatter before starting. Finding, matching the owner's own complaint: EduStation's skills are individually well-written but **fragmented past the point of being practical** — trivial variations of the same underlying capability each got their own folder, while the actual teaching work stayed thin. Concretely:

- **15 folders are the same Nghị định 30/2020 administrative-document template**, parameterized only by document type/occasion: `docs_writer` (the general case: tờ trình/công văn/báo cáo/kế hoạch/biên bản/quyết định) plus 14 near-duplicates — `annual_report`, `correspondence_log`, `directive_letter`, `inspection_plan`, `inspection_report`, `interim_report`, `meeting_minutes`, `school_decision`, `training_plan`, `weekly_schedule`, `yearly_plan`, `admin_petition`, `multi_school_aggregate`, `digital_records`.
- **5 folders are variations of the same CV 5512 lesson/curriculum-planning capability**, differing only in scope: `lesson_plan`, `theme_lesson_plan`, `cross_subject_plan`, `teacher_plan`, `homeroom_plan`.
- **6 folders are variations of the same cognitive-level-matrix assessment-generation capability**, differing only in output shape: `exam_builder`, `review_exam`, `sample_exam`, `tn_thpt_review`, `question_bank`, `review_outline`.
- **2 folders are the same parent-communication task**: `parent_brief`, `parent_letter`.
- **11 folders are pure document/media infrastructure** already covered by Scriptorium's foundation-tier skills, not Teacher-specific at all: `word`/`excel`/`pdf`/`content`/`bilingual_paragraph_merger`/`latex_build` → `office-doc-creator`/`document-ai-structurer`/`translator-en-vi`/`latex-project-bootstrap`; `bulletin_poster`/`edu_infographic`/`visual`/`image_gen_pipeline`/`slide_outline` → `image-generator-gemini`/`mermaid-diagram-designer`/`office-doc-creator`(pptx).
- `docx_rebuild`/`xlsx_repair` (repairing a malformed Office file) are a genuinely new capability not yet in Scriptorium at any tier — flagged as a possible **foundation-tier** gap (not Teacher-specific), not scheduled.
- `course_syllabus`/`research_paper`/`research_proposal`/`thesis_guide`/`essay_contest`/`university_exam_bank` belong to the University Student/Lecturer tiers, not Teacher.
- `skill_creator`/`research`/`campaign_runner`/`_templates` are EduStation's own meta-tooling — Scriptorium already has better equivalents (`skill-creator`, `scout-harvester`).

**Owner's explicit direction on scope (2026-07-26)**: build for what serves actual teaching, not administrative/bureaucratic process. The 15-folder Nghị định 30/2020 administrative-paperwork cluster is **excluded from this tier entirely**, not just deferred — the owner's words: *"đáp ứng cho giáo dục, không đáp ứng cho chính trị, thủ tục rườm rà."* Reasonable consolidated shortlist for what remains (down from ~40 Teacher-relevant folders to ~6 capability clusters):

| Consolidated skill | Replaces (EduStation folders) | Status |
| --- | --- | --- |
| `lesson-plan-builder` | `lesson_plan` + (loosely) `theme_lesson_plan`, `cross_subject_plan`, `teacher_plan`, `homeroom_plan` | **Done** (v0.1.0) — single-lesson CV 5512 structural validator; multi-lesson/interdisciplinary variants not yet covered, noted as a known limitation |
| `assessment-builder` | `exam_builder`, `review_exam`, `sample_exam`, `tn_thpt_review`, `question_bank`, `review_outline` | **Done** (v0.1.0) — built via parallel sub-agent (2026-07-26), reviewed + independently re-tested by the orchestrating session |
| `grading-and-feedback` | `grading`, `primary_remarks`, `report_card_remarks` | **Done** (v0.1.0) — built via parallel sub-agent, reviewed by orchestrating session |
| `competency-rubric-builder` | `competency_rubric` | **Done** (v0.1.0) — built via parallel sub-agent, reviewed + independently re-tested by the orchestrating session |
| `classroom-materials-builder` | `classroom_worksheet`, `homework_sheet`, `learning_game` | **Done** (v0.1.0) — built via parallel sub-agent, reviewed + independently re-tested by the orchestrating session |
| `grade-book-builder` | `grade_book` | **Done** (v0.1.0) — built via parallel sub-agent, reviewed + independently re-tested by the orchestrating session; deliberately hardcodes no official TT22/2021 weight/banding numbers (not found verified in source), left as required caller input |
| `parent-communication` | `parent_brief`, `parent_letter` | **Done** (v0.1.0) — built via parallel sub-agent, reviewed by orchestrating session |
| ~~administrative-paperwork cluster~~ | ~~15 Nghị định 30/2020 folders~~ | **Excluded by owner direction** — not building this |
| `teacher_self_eval` (TT20/2018) | — | Not started, lowest priority (compliance form, not teaching) — the only item remaining on the Teacher-tier shortlist |

### How the 6 parallel skills were built (2026-07-26)

Per owner request ("dispatch các subagent để hoàn thiện song song... rồi bạn duyệt lại một lần"): 6 independent background sub-agents were dispatched in parallel, each given the shared conventions (read `lesson-plan-builder` as the reference pattern, stdlib-only Python, real testing required, no AI/LLM call, explicit EduStation source paths to read for domain knowledge only — never copy orchestration machinery), and each explicitly forbidden from touching `registry/skills.json`/`docs/*.md` to avoid concurrent-write conflicts. Each reported back a finished, self-tested skill folder plus a ready-to-paste registry entry and STATUS.md row.

The orchestrating session then reviewed all 6 before integrating: verified every claimed file actually exists, scanned all 9 new scripts for dangerous patterns (`eval`/`exec`/`subprocess`/network calls — none found, all stdlib-only), and independently re-ran each script against its own bundled asset template to confirm the reported behavior for real (not just trusting the sub-agent's report). All 6 held up under this independent re-check. `security_audit.status` was set to `passed` by the orchestrating session (sub-agents themselves left it `pending`, correctly deferring that judgment) after this review.

### After the education ladder: specializer networks

**Legal is first.** Owner directed jumping straight to Legal after the Teacher tier (skipping University Student/Lecturer tiers for now, 2026-07-26 sequencing). Real survey already collected: `outside_research/research_01_survey.md` (11-item survey, a recent law graduate in a junior legal role) + 2 AI-assisted research reports providing competency/maturity-model framing (`research_01_result_01.md`, `research_01_result_02.md`). This satisfies principle 4 for the legal vertical specifically.

Other industries (Medicine, Finance, ...) require their own real survey before a specializer network starts — no shortcut via brainstormed lists.

### Legal-cluster consolidation survey (2026-07-26)

Surveyed the 11-item practitioner survey + both AI research reports before building, same discipline as the Teacher-tier survey. Consolidated into **5 skills + 1 extension of the existing `translator-en-vi`**, not 9-11 separate skills:

| Consolidated skill | Replaces (survey items) | Status |
| --- | --- | --- |
| `contract-consistency-linter` | items 7, 8 (spelling/format, consistency) | **Done** (v0.1.0) — built first, no external-data dependency |
| `legal-research-brief` | items 1, 10 (initial research, brief statutes) | Not started — must be `grounding: required`, strict-grounding to caller-supplied sources only (no web search), same discipline as `citation-management`'s "why not use an LLM" |
| `legal-citation-checker` | item 2 (cite Điều/Khoản/Điểm + hiệu lực status) | Not started — **real data gap**: no free Vietnamese legal-document API exists (unlike CrossRef for academic citations) to verify a statute's real-world hiệu lực status. Recommended scope for v0.1.0: citation-**format** validation only (well-formed, internally consistent Điều/Khoản/Điểm syntax), NOT hiệu lực verification, until/unless a real queryable source is supplied |
| `legal-form-filler` | items 3, 4, 5 (form filling, form suggestion, dossier completeness) | Not started — **real data gap**: no government checklist/template data available to this project. Recommended scope: a generic checklist-against-provided-documents + template-placeholder-filling engine where the checklist/template is caller-supplied input, never hard-coded (mirrors `grade-book-builder`'s refusal to hardcode unverified official numbers) |
| `contract-risk-log` | item 6 (contract risk review) | Not started — recommended as a structured issue-log scaffold (risk category / clause location / concern / recommended action), mirroring `peer-review`'s claim-evidence-matrix pattern, rather than a full auto-risk-detector claiming legal judgment it can't deterministically make |
| `translator-en-vi` + legal glossary | item 9 (legal translation) | Not started — extend the existing general-tier `translator-en-vi` with a `references/legal-glossary.json` + a terminology-consistency check script, not a whole new skill (dependency relationship, same pattern as `citation-management`/`office-doc-creator` reuse elsewhere) |

Building **sequentially this round** (owner: "làm tuần tự từng cái nhé"), not via parallel sub-agent dispatch like the Teacher tier — one skill at a time, in the order above.

A third real gap noted but not yet acted on: the PII-anonymization pattern (local-only real-name↔code mapping, never sent to an LLM) now has 2 precedents in this repo (`grading-and-feedback`'s `anonymize_roster.py`, `peer-review`'s confidentiality intake gate) and would likely be needed a 3rd time for legal skills touching client data — a candidate for promotion to a shared foundation-tier utility if/when it's actually needed here, not built preemptively.

## More flexible repo structure (owner confirmed)

Not everything has to live inside `skills/`. Free to add directories at root (`scripts/`, a shared `venv`...) if convenient — treat Scriptorium like a normal project, not a rigid mold containing only `skills/`.
