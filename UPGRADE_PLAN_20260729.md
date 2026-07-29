# Upgrade Plan — Scriptorium (2026-07-29)

> **Document Purpose**: Execution checklist for downstream agents (Claude Code, Codex CLI, Kimi, Amp, or any other harness working in this repo). Rewritten 2026-07-29 from a strategy narrative into a checklist so progress is trackable item-by-item and sub-step-by-sub-step. Each item still carries the reasoning behind it (from `request.md`'s discussion round + owner direction) — do not strip that when checking boxes, it's what keeps a later session from re-deriving the same decision.

**Read `CLAUDE.md` first.** It is the mandatory system entry point — non-negotiable principles, the 9-step pipeline, registry conventions, Windows PowerShell/`uv` constraint. This plan does not override anything in it.

---

## 0. North Star & positioning (context, not a checklist item)

> *"Scriptorium aims to become the canonical knowledge packaging, verification, and deployment layer for portable AI skills — enabling individuals and organizations to transform tacit domain expertise into reusable, verifiable capabilities across any agent runtime."*

- Not competing with agent runtimes (Claude Code, Codex, Kimi, Amp, OpenHands) — Scriptorium sits one layer above, in **Knowledge Packaging & Deployment**.
- Marketing/framing shift: not *"we have 38 skills"* but *"turn your expertise into a portable, verified AI capability."* 38 skills is not a moat by itself — see item 6 below for why the pipeline (not the count) is the actual asset.
- Roadmap-inflation risk (flagged directly in `request.md`'s discussion, point 9): a solo founder's biggest risk here is dispersing across Foundation/Teacher/Student/Parent/University/TA/Researcher/Legal/Design/Workspace/Tutorial simultaneously, not running out of ideas. Sequencing below is deliberately sequential-with-priority, not "do all 7 items at once."

## Current inventory (40 skills, as of 2026-07-29)

Full detail: `docs/STATUS.md`. Registry: `registry/skills.json`. Stage-4 (quality-eval) applicability per skill is scoped — see `docs/STATUS.md`'s "Stage 4 applicability" table and `registry/SCHEMA.md`'s `quality_score.stage4_required` field (owner decision 2026-07-29): only expert-elicited niche-specializer skills and skills ingesting uncontrolled external input need it; foundation/general-capability skills are exempt by design.

- **Pipeline & Infrastructure (7)**: `skill-creator`, `skill-exporter`, `security-audit`, `quality-eval`, `scout-harvester`, `license-compliance-check`, `dedup-novelty-check`.
- **Foundation & General Utilities (19)**: `document-ai-structurer`, `pii-masking`, `personal-profile-manager` (Item 1, built 2026-07-29), `deep-research`, `literature-review`, `citation-management`, `hypothesis-generation`, `peer-review`, `exploratory-data-analysis`, `translator-en-vi`, `latex-project-bootstrap`, `typst-bootstrap`, `image-generator-gemini`, `office-doc-creator`, `mermaid-diagram-designer`, `browser-web-renderer`, `xelatex-bootstrap`, `pandoc-bootstrap`, `python-env-bootstrap`.
- **Teacher Tier (7)**: `lesson-plan-builder`, `assessment-builder`, `grading-and-feedback`, `competency-rubric-builder`, `classroom-materials-builder`, `grade-book-builder`, `parent-communication`.
- **Student Tier (1)**: `study-plan-builder`.
- **Vietnamese Legal Specializer Network (6)**: `contract-consistency-linter`, `legal-research-brief`, `legal-citation-checker`, `contract-risk-log`, `legal-form-filler`, `legal-web-search`.

**Before starting any item below**: query `registry/skills.json` by `domain`/`task_type`/`object_type` for overlap — if an existing skill already covers ≥80% of a new candidate's scope, extend/version it instead of creating a parallel entry (`dedup-novelty-check` discipline).

---

## Working rule for every new skill type in this plan

Before running `skill-creator` on any brand-new skill type introduced by this plan (not a version bump of an existing skill), do the **scout step first, not last** — owner directive 2026-07-29: *"Search và clone các repo tiêu biểu cho cùng một chủ đề và tham khảo trước khi tạo kiểu skill đó."*

- [ ] Search for 2-4 representative real-world repos/projects on the same topic (`WebSearch`, or `scout-harvester`'s `github_scout.py` for GitHub specifically).
- [ ] Shallow-clone the most relevant 1-3 into `outside_research/references/<topic>/` via `scout-harvester`'s `clone_candidate.py` (never inside `skills/`, never committed as a dependency — reference-only).
- [ ] Run `license-compliance-check` on anything whose patterns/code might get adapted (not just wholesale-copied) — per `CLAUDE.md` principle 5, harvesting/adapting goes through this gate before `skill-creator`, license-debt-eligible unless the source has an explicit no-redistribution clause.
- [ ] Record what was found/adapted/rejected in the skill's own `SKILL.md` (`metadata.elicited_from` or an explicit "Reference material" note) and in this file's checklist, not just in agent scratch memory — so a later session can see the grounding without re-deriving it.
- [ ] Only then run `skill-creator`, following each item's specific elicitation tier below (per `CLAUDE.md` principle 4's three-tier model: infra/bootstrap → no interview needed; general-capability → public-source grounding sufficient; niche specializer → mandatory real elicitation source).

---

## Item 1 — Personal Profile & Behavior Adaptation Skill Cluster

**Tier**: General-capability (personalization/UX pattern is publicly well-documented — no expert interview needed; grounded directly in owner's own stated pilot need).
**Status**: Built as `personal-profile-manager` v0.1.0 (2026-07-29). See `docs/STATUS.md`'s row for full real-verification detail.

- [x] Scout: surveyed AWS CLI's config/credentials-file split and cookiecutter's variables-file pattern (lightweight web survey, no clone — deliberately kept stdlib-only rather than adopting a templating dependency).
- [x] Design `personal/profile.json` schema: identity, organization, title, tax ID, contact — fields cross-checked against `legal-form-filler`/`office-doc-creator`/lesson-plan-style input schemas rather than invented from scratch.
- [x] Build `personal-profile-manager`: `init_profile.py` (scaffold, overwrite-protected) + `validate_profile.py` (required-section/field check) + `autofill.py` (generic caller-supplied field_map engine, unresolved fields reported by name, never invented).
- [x] Build the writing-style adaptation half: `propose_style_update.py` turns a feedback log into a proposal Markdown block — proposal only, never auto-applies to `CLAUDE.md`/`AGENTS.md`/a system prompt.
- [x] Privacy-by-default: `/personal` added to root `.gitignore`. `personal/README.md` explaining the protection is still open — create it alongside the first real profile a user actually makes (not fabricated here without a real profile to document).
- [x] Verify real: all 4 scripts run against both clean and deliberately-broken fixtures (see `docs/STATUS.md` row for the exact cases) — malformed input, missing sections, typo'd field-map paths, nested-object-instead-of-leaf paths, empty entries lists all correctly refused/reported.
- [x] Register in `registry/skills.json` (`stage4_required: false` — foundation/general-capability, no expert elicitation, no uncontrolled external input) and `docs/STATUS.md`.
- [ ] Open follow-up: not yet wired into any downstream skill's real input pipeline (e.g. actually auto-filling a real `legal-form-filler` run) — verified standalone only this round.

## Item 2 — Project Workspace Scaffolder (`project-workspace-initializer`)

**Tier**: General-capability, but grounded in a **real pilot**, not just public convention — treat the elicitation bar as closer to niche-specializer given it's modeling one real non-tech user's actual workflow.
**Elicited from**: real non-tech user workflow testing, `d:/my-workspace` deployment for a legal practitioner (per `docs/ROADMAP.md`).
**Status**: Built as `project-workspace-initializer` v0.1.0 (2026-07-29). See `docs/STATUS.md`'s row for full real-verification detail.

- [x] Scout: lightly surveyed `cookiecutter`'s template+variables convention (public pattern, web survey only — not cloned, kept stdlib-only since a fixed subdir set + prompts file doesn't need a templating engine).
- [x] Re-review the actual `d:/my-workspace` deployment — **not accessible on this machine this session** (path no longer exists); fell back to the already-recorded workflow description in `docs/ROADMAP.md`'s 2026-07-29 entry as the elicitation record instead of inventing one. Flagged in the skill's own `elicited_from`, not silently papered over.
- [x] Design `assets/templates/` — one real profession template built (`legal-practitioner`); deliberately no other templates invented without a real pilot behind them.
- [x] Build the scaffolder script (`scaffold_workspace.py`): `project_YYYYMMDD_NN/` with template-declared subdirectories; collision-safe date+sequence numbering verified real (see STATUS.md).
- [x] Build `PROJECT.md` generator: folded into the same script — renders the template's `project_md_prompts` as headed instruction blocks.
- [x] Verify real: same-day double-scaffold sequencing, historical `--date` sequencing, malformed-template refusals, nonexistent-path refusal all verified (see STATUS.md).
- [x] Register in `registry/skills.json` + `docs/STATUS.md`.

## Item 3 — Role Capability Layer (8 independent roles → merged to 7, see below)

**Tier**: Mixed — Teacher/Student already-built precedent is general-capability tier (public curriculum/pedagogy grounding, `CLAUDE.md` principle 4). New roles below inherit the same tier **only if** their skill's core knowledge is genuinely publicly documented.
**Status**: Built (2026-07-29) via 6 parallel background agents, one per role cluster, each independently re-verified by the orchestrating session (`validate_skill.py` + syntax compile + security grep across all 17, plus real re-runs of sample scripts from 2 of the 6 batches). Full detail: `docs/STATUS.md`'s "Item 3" section.

**Post-build reclassification (2026-07-29, owner-directed, `docs/DECISIONS_PENDING.md` resolved items 5-6)**:
- **Student (K12) and University Student merged into one Student/Learner tier** — `docs/specs/STRATEGY_SPEC.md` §5.1 rewritten. See §3a/3d below, now presented together.
- **`socratic-concept-helper` PAUSED** — built, then paused after a same-day `deep-research` follow-up (`outside_research/research_06_socratic_helper/`) confirmed the STRATEGY_SPEC-flagged survey gap wasn't closed by further public research, plus a separate structural objection (real-time student-direct operation doesn't match how K12 students access AI). `registry/skills.json` gained `operational_status`, `skill-exporter` v0.2.1 hard-excludes it from export.

### 3a + 3d. Student / Learner (merged K12 + University, 2026-07-29)
- [x] Scout: `outside_research/research_02/research_02_result_01.md` (Socratic-restraint pattern, AI-homework-harm research) for K12-shaped skills; public academic-writing/citation/RACI conventions for university-shaped skills.
- [x] Built `exam-ready-scaffold`, `reading-note-structurer` (K12-shaped; each got a "Who operates this" section post-merge clarifying the operator is typically a teacher/tutor/parent, not the K12 student self-operating an agent CLI).
- [x] Built `socratic-concept-helper` — **then paused**, see above. Code kept (the restraint-linter may be reusable once a real operator model is settled), not registered as production-ready.
- [x] Built `essay-structure-scaffold`, `academic-source-finder` (explicitly a protocol/validator, never a search service itself — same non-negotiable as `deep-research`/`legal-web-search`), `group-work-coordinator` (university-shaped).
- [x] `study-plan-builder` (pre-existing) also got a "Who operates this" clarification, doc-only version bump.
- [x] Registered all 6 new skills + verified real (see `docs/STATUS.md`).

### 3b. Parent / Guardian
- [x] Scout: checked overlap against existing `parent-communication` (Teacher-tier) first — confirmed different direction (parent→school vs. teacher→parent), well under 80% overlap.
- [x] Built `parent-school-communicator`, `home-study-environment-guide` (screen-time/sleep numbers verified via live web search, not memory recall), `student-progress-tracker`.
- [x] Registered + verified real.

### 3c. School Admin / Academic Coordinator
- [x] Scout confirmed: no real school-administrative-workflow source available, same category of gap the Teacher tier already excluded.
- [x] **Not built** — flagged as an open gap in `docs/specs/STRATEGY_SPEC.md` §5.1's table, not fabricated.

### 3e. Teaching Assistant / Graduate Student
- [x] Scout: rubric-calibration/norming literature (Stevens & Levi), Tukey's IQR convention, ACS lab-safety guidelines, Creswell's proposal-structure literature.
- [x] Built `ta-grading-rubric-linter`, `lab-practicum-guide`, `dissertation-proposal-scaffold`.
- [x] Registered + verified real.

### 3f. Lecturer & Researcher
- [x] Scout + overlap check against the existing 5 research skills — confirmed genuinely new (no overlap).
- [x] Built `academic-grant-proposal` (NIH SF424/NSF PAPPG budget-justification structure), `manuscript-journal-formatter` (IEEE/APA citation-format checking, real style guides cited).
- [x] Registered + verified real.

### 3g. Lifelong Learner / Upskilling Professional
- [x] Scout: career-development/skill-taxonomy literature, real certification-body exam blueprints.
- [x] Built `upskilling-roadmap-builder` (directly imports `study-plan-builder`'s scheduling core — a real registry dependency, not a duplicate), `certification-exam-prep`, `knowledge-gap-analyzer`.
- [x] Registered + verified real.

## Item 4 — Light Design Skill Cluster

**Tier**: General-capability but explicitly grounded in 2 real reference projects — treat those as the elicitation source, not invented layout theory.
**Elicited from**: `D:/elix/temp_project_20260728`, `D:/Document/May052026`.
**Scope discipline** (explicit owner/discussion boundary, `request.md` point 8): deterministic SVG/layout utilities only. **Do not** expand into general image generation, Figma-clone territory, or anything competing with Photoshop/Illustrator — that's a red ocean and off-thesis for Scriptorium (pure artifacts, no AI backend, deterministic-first).
**Status**: Built as 4 skills v0.1.0 (2026-07-29). See `docs/STATUS.md` rows for full real-verification detail.

- [x] Re-surveyed `D:/elix/temp_project_20260728` (real brand-data.json: color-role priority system, real client feedback on CTA emphasis and orphan icons) and `D:/Document/May052026` (real `component_types.md` zone taxonomy + `rules.md`) directly — extracted concrete rules rather than re-deriving generically.
- [x] Scout: decided AGAINST adopting a Python SVG-generation library — hand-built SVG string templating (stdlib only) was sufficient for labeled placeholder rectangles, no genuine need for a dependency (per CLAUDE.md's stdlib-first discipline).
- [x] Built `svg-poster-builder` — deterministic SVG layout engine, A1/A4, 6-type zone taxonomy from the real `component_types.md` schema.
- [x] Built `brand-identity-linter` — 3 checks traced to real client-feedback findings (color-role completeness, CTA/contact emphasis, orphan-icon detection).
- [x] Built `slogan-copy-linter` — length cap, banned-phrase scan, all-caps warning.
- [x] Built `light-logo-arranger` — named-anchor coordinate calculator with exclusion-zone collision refusal.
- [x] Verified each real: see `docs/STATUS.md` rows for exact test cases (all 4 fixtures use generic/anonymized data structurally matching the real reference projects, not the real clients' actual business data — privacy discipline applied deliberately).
- [x] Registered all 4 in `registry/skills.json` + `docs/STATUS.md`, `domain: general`.

## Item 5 — Upgrade `skill-creator` with Tacit Knowledge & Document Distillation

**Tier**: Infrastructure/bootstrap (upgrading an existing meta-skill) — grounded in a real cloned reference, no expert interview needed.
**Reference already scouted**: `virgiliojr94/book-to-skill` (MIT), cloned to `outside_research/references/book-to-skill/`.
**Status**: Built as `skill-creator` v0.4.0 (2026-07-29). See `docs/STATUS.md`'s row for full real-verification detail.

- [x] Read the cloned `book-to-skill` reference's SKILL.md in full (modes, step 6-9 output shape, component_types-style token-budget matrix) — confirmed the real 4-mode taxonomy and chapters/glossary/patterns/cheatsheet shape directly from the source, not from a summary.
- [x] License-compliance-check on `book-to-skill` — MIT confirmed directly (`LICENSE.md`), cleared, already recorded from the earlier scouting session (2026-07-27).
- [x] Designed the scaffolding/validation split honestly: chapter CONTENT (frameworks, decision trees, worked examples) is inherently agent-authored (requires reading comprehension a script can't do) — what got built deterministically is the scaffolding (`scaffold_distillation.py`) and the structural/budget validation (`validate_distillation.py`), consistent with this project's "script decides pass/fail mechanically, judgment stays with the agent" discipline.
- [x] On-demand reference scaffolding: master `SKILL.md` + `chapters/`, token budgets checked via an explicitly-approximate heuristic (`word_count*1.3`), never presented as an exact tokenizer count — did NOT repeat the reference repo's unverified 24x-51x reduction claim as our own without measuring it locally; measured directly instead (real test distillation's SKILL.md body came out at ~42 tokens, small because detail lives in on-demand chapters).
- [x] Implemented all 4 operation modes as documented agent-executed steps in `SKILL.md` (Full Conversion, Analyze Only, Generate from Prior Analysis, Update/Fold-in) — mode routing itself doesn't need a script, only the scaffolding/validation steps within Full Conversion do.
- [x] Supporting artifact scaffolding: `glossary.md`/`patterns.md`/`cheatsheet.md` stub generation built into `scaffold_distillation.py`.
- [x] Verified real: scaffolded a 2-chapter distillation, filled it with real content distilled from `registry/SCHEMA.md` (not synthetic placeholder text), validated clean end-to-end; 5 violation cases (leftover placeholder, dangling chapter reference, oversized SKILL.md, missing supporting file, empty chapters dir) and the scaffold's overwrite-protection all separately verified.
- [x] Bumped `skill-creator` to v0.4.0 in `registry/skills.json` + `docs/STATUS.md`, documented what changed (Document Distillation Mode) and why, plus fixed a stale security-audit note ("Pure instructional, no script" — no longer true since v0.3.1 already had 2 scripts before this round).

## Item 6 — Upgrade `skill-exporter` to a Knowledge Deployment Engine

**Tier**: Infrastructure (upgrading an existing meta-skill).
**Reframe** (from the `request.md` discussion, points 1-8): `skill-exporter` is not a zip utility, it's the layer that turns a registry (knowledge repository) into a working capability bundle for one specific user/task/environment — "Đúng người - Đúng việc - Tinh gọn tối đa" (right person, right task, maximally lean). The pipeline this implies:

```
Registry → Dependency Resolution → Audience Matching → License Filter →
Security Filter → Bundle Optimization → skills.zip
```

**Status**: Built as `skill-exporter` v0.2.0 (2026-07-29). See `docs/STATUS.md`'s row for full real-verification detail.

- [x] Built `skills.lock`: `skill_id -> {version, content_sha256}` for every included skill, written into every export. A plain content hash (not a package-registry version pin, since skills have no such registry) — verified real via `verify_lock.py` catching a deliberately tampered file.
- [x] Built `MANIFEST.md` (already existed, now also records `requested`/`dependency of X` per skill) + new `dependency-tree.md` (the same reasoning as its own dedicated file).
- [x] Built negative-dependency/exclusion rules: `--exclude <skill_id>` or `--exclude axis:value` (e.g. `domain:education`), repeatable. Simpler than the discussion transcript's glob example (`education/*`) — exact axis:value match only, documented as a known limitation, extend to glob matching if a real need surfaces.
- [x] Audience matching past role alone: not built as a separate mechanism — the discussion's "User + Task + Environment" point is still served by the calling agent's own interview feeding `list_candidates.py`'s existing domain/task_type/object_type filters, now sharpened by `--exclude` for narrowing a bundle the filters alone over-match. Documented explicitly as a known limitation rather than claiming a new automated matching engine that doesn't exist.
- [x] Verified real: `--exclude` correctly refuses when it would break a hard dependency (tested 2 levels deep, confirming the refusal chains rather than only checking one hop); `--exclude domain:legal` correctly narrows a 2-skill bundle to 1; `skills.lock` reproducibility verified via `verify_lock.py` against both an unchanged and a deliberately tampered copy.
- [x] Bumped `skill-exporter` to v0.2.0, documented the reframing (zip utility -> Knowledge Deployment Engine) in `docs/STATUS.md` and the skill's own `SKILL.md` `elicited_from`.

## Item 7 — Non-Tech Tutorial Guides

**Tier**: Documentation, not a skill — general-capability, no elicitation gate applies (it's a guide about using Scriptorium's own artifacts, not a new capability).
**Status**: Built as `docs/guides/NON_TECH_USER_GUIDE.md` (2026-07-29).

- [x] Drafted `docs/guides/NON_TECH_USER_GUIDE.md`: step-by-step, plain-language, how to receive/import/run a `skill-exporter` bundle. Checked `registry/skills.json`'s `harness_compatibility` field first (currently only `claude-code` appears anywhere in the registry) — the guide is explicit that only Claude Code is directly verified, other harnesses get general "should work per the open spec, not verified here" guidance rather than an unverified compatibility claim, per `CLAUDE.md` principle 3.
- [x] Grounded the walkthrough in a real bundle, not a hypothetical one: actually ran `export_bundle.py` for a real 5-skill Legal-cluster request during this guide's own writing (2026-07-29) — the resulting 7-skill bundle (5 requested + 2 auto-included dependencies) and its real `MANIFEST.md`/`dependency-tree.md`/`skills.lock` contents are what the guide describes, not an imagined example.
- [ ] Not done: real screenshots (text-only guide for now — no screenshot-capture tooling used this session) and a genuinely non-technical reviewer walkthrough test. Flagged as an open follow-up, not silently skipped.

---

## Execution notes for downstream agents

1. Read `CLAUDE.md` first — non-negotiable.
2. Check `registry/skills.json` + `docs/STATUS.md` + `docs/ROADMAP.md` before writing any code — avoid duplicate/overlapping skills.
3. Follow the 9-step pipeline per new skill: Research → Elicit → `skill-creator` → Quality Eval (only if `stage4_required` — see `docs/STATUS.md`) → Security Audit (always, separate gate) → Scout/Harvest → License Check → Dedup Check → Registry.
4. No AI API calls inside any skill — skills are stdlib/script-backed validators, generators, or protocols the calling agent executes with its own tools.
5. Validate every new/changed `SKILL.md` with `skills/skill-creator/scripts/validate_skill.py`.
6. Run `security-audit` on every new skill before marking it `passed` in the registry — never skip, never merge with quality eval.
7. Scout representative repos/projects **before** `skill-creator` for any genuinely new skill type (see "Working rule" above) — this is a recommended practice going forward, not just a one-off for item 5.
