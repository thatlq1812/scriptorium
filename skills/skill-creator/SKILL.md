---
name: skill-creator
description: Standardize procedural knowledge already elicited from a real source (an expert, or the owner's tacit knowledge) plus grounded research, into a portable Agent Skill following the agentskills.io open spec (6-field frontmatter). Use when elicited-process input + research are ready for a specific, repeatable procedure. Do NOT use to self-infer a new skill without elicited/research input — a self-generated skill that skipped elicitation has been measured as "no benefit on average" (SkillsBench).
license: MIT
compatibility: Portable per the agentskills.io open spec (6-field frontmatter, no extensions). Verified running clean: Claude Code (2026-07-26). Not yet verified: OpenAI Codex CLI, Kimi Code CLI, Antigravity CLI — do not mark compatible until tested directly.
metadata:
  domain: meta
  task_type: skill-authoring
  risk_tier: N2
  pipeline_stage: 3
  source: self-authored
  elicited_from: "Owner tacit knowledge from the EduStation postmortem (docs/archive/pre-spec-2026-07-26/handoff.md) + deep research session 2026-07-26, distilled into docs/specs/STRATEGY_SPEC.md"
  version: 0.4.0
  changelog_0_4_0: "Added Document Distillation Mode (UPGRADE_PLAN_20260729.md Item 5): scripts/scaffold_distillation.py (deterministic chapters/+glossary.md+patterns.md+cheatsheet.md+master-SKILL.md scaffolding, overwrite-protected) and scripts/validate_distillation.py (chapter-naming, leftover-placeholder, dangling-cross-reference, and approximate token-budget checks -- token counts are an explicit word-count*1.3 heuristic, never presented as exact). Directory shape adapted from outside_research/references/book-to-skill (MIT, license-compliance-checked 2026-07-27) -- scaffolding/validation automated, actual chapter content generation stays agent-authored (requires real reading comprehension of the source document, same division of labor as the rest of this skill: never invents domain content). Verified real end-to-end: scaffolded a 2-chapter distillation, filled it with real content distilled from registry/SCHEMA.md, validated clean; separately verified 4 violation cases (leftover placeholders, dangling Ch NN reference as a non-blocking warning, oversized SKILL.md body, missing supporting file) and the overwrite-protection refusal."
  changelog_0_3_1: "Added scripts/validate_skill.py: a mechanical validator for the 6-field spec + Scriptorium's required metadata fields (name==folder, description/compatibility length caps, elicited_from non-empty, risk_tier/task_type/source enum checks), stdlib-only. Closes a gap found comparing against github.com/anthropics/skills' skill-creator/scripts/quick_validate.py during this session's core-skill-package research round: this skill's own SKILL.md documented these structural constraints in prose but had no script gating them, relying entirely on an agent reading carefully. Running it retroactively against the full registry found 19 pre-existing real violations (compatibility field verification narrative accumulated past the 500-char cap over many sessions) -- all fixed the same session (moved to a 'Verified' section in each skill's own body)."
  adapted_from: "The 'pushy description' pattern + trigger eval set adapted from github.com/anthropics/skills skills/skill-creator (Apache-2.0), cleared via skills/license-compliance-check on 2026-07-26. The gold-template + scaffold-script pattern adapted from D:/elix/edustation/skills/_templates/ (owner's prior project) -- kept the copy-a-skeleton principle and REQUIRED/CHOOSE comment legend, dropped the harness-specific tier/CI-enforcement machinery. validate_skill.py (v0.3.1) adapted from the same anthropics/skills skill-creator's quick_validate.py -- pattern/structure only (allowed-keys check, name/folder match), rewritten from scratch in Scriptorium's own field set, no code copied verbatim. Document Distillation Mode (v0.4.0) adapted from outside_research/references/book-to-skill (MIT) -- directory shape and mode taxonomy only, scripts and prose rewritten from scratch in Scriptorium's own conventions, no code copied verbatim."
---

# skill-creator

The meta-skill that produces a `SKILL.md` for another skill in Scriptorium. This is step 3 in the bootstrap pipeline (`docs/specs/STRATEGY_SPEC.md` §3) — it comes AFTER research and elicit-tacit-process, never before.

## Precondition — check before running

Before writing a single line of SKILL.md, confirm both of the following exist, and note their source explicitly:

1. **Elicited tacit process** — a process extracted from a real source (a practicing expert, or Scriptorium's own owner describing concrete experience), not the model's own inference. If this doesn't exist yet, STOP — go back to the elicit step; never invent a process and treat it as valid input.
2. **Grounded research** — verifiable reference sources (documentation, benchmarks, law, industry standards), not unverified interpolated knowledge.

If either is missing, this step's output falls into the "self-generated skill" bucket — measured by SkillsBench as no improvement over having no skill at all. Never create a skill in that state.

## Stick to the 6-field spec — never invent extra fields

Frontmatter has exactly 6 keys: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Every Scriptorium-specific field (domain, task_type, risk_tier, pipeline_stage, elicited_from, harness_verified...) goes inside `metadata`, never at the top level.

- `name` — required, ≤64 chars, lowercase letters/numbers/hyphens only, MUST match the parent folder name under `skills/`.
- `description` — required, ≤1024 chars. State BOTH: what the skill does, AND when to use it / when not to (helps the consuming agent pick the right skill among several). This is the primary triggering mechanism — the consuming agent decides whether to use a skill based on `description` alone (it hasn't read the body yet). The general tendency is to **under-trigger** (the agent skips a skill it should have used): write the description slightly "pushy" instead of neutral — spell out different contexts/phrasings a user might type, not just one sample sentence. Before finalizing the description, generate 8-10 "should trigger" questions + 8-10 "should not trigger" questions (especially near-misses — questions using similar keywords that actually need a different skill) and self-check whether the description discriminates correctly; fix it if not.
- `license` — SPDX identifier. If the skill was harvested from an outside source, the license must match the original and have passed license-compliance-check (pipeline step 7) — never unilaterally switch it to MIT.
- `compatibility` — ≤500 chars. List only harnesses that have ACTUALLY been verified running. A harness that hasn't been tested must not be listed, even if a vendor showcase claims support (see `docs/archive/pre-spec-2026-07-26/raw_research.md` §1 — Kimi Code CLI is absent from the official showcase even though many secondary sources claim it's supported).
- `metadata` — a free key-value map, use at minimum Scriptorium's 5 standard fields: `domain`, `task_type`, `risk_tier` (N1-N5, per `registry/SCHEMA.md`), `source` (`self-authored` or `harvested`), `elicited_from` (a short description of the elicited knowledge source — this field must never be empty).
- `allowed-tools` — marked Experimental in the spec. Only add it when there's a concrete safety reason to restrict tools (e.g. a high risk-tier skill shouldn't have arbitrary file-write access). Don't add it by default "just in case."

## Scaffold from a gold template — don't write SKILL.md from a blank file

Copy from a template in `templates/` instead of authoring from scratch each time — reduces variance/errors and speeds up creation. Decide which:

- **Standalone** (`templates/standalone_skill/`) — a user/agent invokes it directly for a deliverable. Mirrors `document-ai-structurer`, `office-doc-creator`, `image-generator-gemini`.
- **Dependency** (`templates/dependency_skill/`) — infrastructure another skill leans on, not invoked directly for a deliverable. Mirrors `python-env-bootstrap`, `license-compliance-check`, `dedup-novelty-check`.

```bash
python skills/skill-creator/scripts/scaffold_skill.py <skill_id> --template standalone_skill
```

This only automates the folder/file mechanics (copies the template, substitutes `<skill_id>`) — it does NOT skip the precondition above. Every remaining `<...>` slot in the copied `SKILL.md` still needs filling from real elicited input + research, and every `<!-- -->` comment block must be deleted before the skill ships.

See `templates/README.md` for the full rationale (adapted from `D:/elix/edustation/skills/_templates/` — the owner's prior project — keeping the copy-a-skeleton principle, dropping the harness-specific machinery).

## Readiness check before handing off to quality-eval

Before anything else, run the mechanical validator:

```bash
python skills/skill-creator/scripts/validate_skill.py skills/<skill_id>
```

This checks the 6-field spec, `name`==folder, `description`/`compatibility` length caps, and that `metadata.elicited_from`/`risk_tier`/`task_type`/`source` are present and valid — deterministically, so a weaker reviewing agent doesn't have to remember every constraint above by reading carefully. Exit 0 = passes structural validation. This is a floor, not the full bar — it doesn't check content quality (that's stage 4) or safety (stage 5).

If the skill's own `SKILL.md` body references a script (e.g. "run `scripts/foo.py`"), that script MUST exist and actually work — never leave a stub, a `NotImplementedError`, or a script that was described in prose but never written. Before calling a skill "created," run it once yourself on a trivial real input and confirm the output matches what the SKILL.md claims. A skill whose documented behavior doesn't match its actual behavior is worse than no skill — it actively misleads the next agent that reads it.

## Structural constraints

- The entire SKILL.md must stay under 500 lines.
- The instructions section (body after frontmatter) must stay under 5000 tokens — if the process is long, split the detail into a supporting file in the same skill folder and reference it from SKILL.md (progressive disclosure); don't cram everything into one file.
- Don't write in a narrative style — write as instructions another agent can follow without needing to ask clarifying questions.

## Document Distillation Mode — turning a book/manual/document folder into an on-demand-reference skill

A separate mode for a different input shape than the rest of this file: instead of an already-elicited procedural process, the input here is a large document (a book, manual, or document folder) whose knowledge needs distilling into a skill an agent can load progressively, not all at once. Directory/file shape (`chapters/ch<NN>-<slug>.md` + `glossary.md`/`patterns.md`/`cheatsheet.md` + a small master `SKILL.md` index) is adapted from a real, cloned, license-cleared reference project (`outside_research/references/book-to-skill`, MIT, license-compliance-checked 2026-07-27) — not invented from scratch. **What's automated here is only the scaffolding and structural validation** (deterministic, scripted); the actual chapter content — frameworks, mental models, worked examples, decision rules — requires real reading comprehension of the source document and is agent-authored, same division of labor as the rest of skill-creator (this tool never invents domain content, it structures/validates content a human or agent supplies).

### 4 modes (route based on what's asked)

1. **Full Conversion** (default) — given source document path(s), scaffold + write every chapter + supporting file + master index in one pass.
2. **Analyze Only** — read the source, produce a structured extraction outline (chapters found, frameworks/concepts identified per chapter) for review; do NOT scaffold/write files yet. Use when the user wants to review the plan before committing to full generation.
3. **Generate from Prior Analysis** — given an existing Analyze-Only outline, scaffold + write from it directly (skip re-reading the source).
4. **Update / Fold-in** — given new source material and an existing distilled skill, add new chapter(s) or revise existing ones; re-run the validator afterward to confirm nothing broke.

### Full Conversion steps

1. Read the source document(s) in full. Identify chapter/major-section boundaries.
2. Scaffold the structure:
   ```bash
   python skills/skill-creator/scripts/scaffold_distillation.py <skill_id> --chapters <n> [--force]
   ```
   Refuses on an existing target without `--force` — same overwrite-protection convention as `scaffold_skill.py`.
3. For each chapter stub in `chapters/`, replace every `<...>` placeholder with real content extracted from the corresponding section of the source: Core Idea, Frameworks Introduced (preserve the author's exact naming — "The 5 Whys" is not interchangeable with "ask why multiple times"), Key Concepts, Key Takeaways, Connects To (only reference a `Ch NN` that actually exists in `chapters/`). Rename each file from the `ch<NN>-untitled.md` stub name to a real slug (`ch01-five-whys.md`, not `ch01-untitled.md`) — the validator's naming check only requires the `chNN-<slug>.md` shape, not the literal word "untitled".
4. Fill `glossary.md` (alphabetical, `**Term** — definition (Ch NN)`), `patterns.md` (concrete techniques, `## Pattern Name` + When to use/How/Trade-offs), `cheatsheet.md` (decision rules and thresholds, not bare term/definition rows — that's what the glossary is for).
5. Fill the master `SKILL.md`'s frontmatter (real `description`, `elicited_from` naming the actual source document, `grounding: required` since every claim traces to the source) and its Chapters section (one line per chapter, most important first — this file is always loaded, chapters are loaded on-demand, and truncation on overflow cuts from the end).
6. Validate:
   ```bash
   python skills/skill-creator/scripts/validate_distillation.py <skill_dir>
   ```
   Exit 0 = valid. Checks (all real, mechanical, not a quality judgment): every chapter file matches `chNN-<slug>.md` naming; no leftover unfilled `<...>` placeholder in any chapter or the master SKILL.md; every `Ch NN` cross-reference resolves to a real existing chapter file (warns, doesn't block — a chapter written before a later one it references isn't necessarily wrong, just needs a human glance); the master SKILL.md body and each chapter file stay under a token budget (**approximate** — `word_count * 1.3`, a rough heuristic since this project has no tokenizer dependency; never read the reported number as exact); all 3 supporting files exist and are non-empty.
7. Run `validate_skill.py` too (the standard 6-field-spec check) — Document Distillation Mode output is still a normal Scriptorium skill and must pass both validators, not just the distillation-specific one.

### What Document Distillation Mode does NOT do

- Does not decide chapter content itself — no LLM call inside any script here; the calling agent reads the source and writes the content, same as every other skill in this registry never calling an AI API internally.
- Does not enforce an exact token count — the budget check is a rough approximation, deliberately documented as such rather than presented with false precision.
- Does not merge/dedupe overlapping distilled skills automatically — if a new source substantially overlaps an already-distilled skill, that's the same dedup-novelty-check discipline as any other new skill candidate, not something this mode special-cases.

## What skill-creator does NOT do

- Doesn't grade the quality of the skill it just created — that's step 4 (quality evaluation loop), run separately, on ≥2 verified harnesses.
- Doesn't audit the security of the skill it just created — that's step 5 (security audit), a separate pipeline stage, never merged with step 4 (`docs/specs/STRATEGY_SPEC.md` §7 point 2).
- Doesn't decide on its own that a skill is "ready to use" — that status is only set when `registry/skills.json` has a non-null `quality_score` AND `security_audit.status = "passed"`.

## skill-creator's output

1. A `skills/<name>/SKILL.md` folder (plus supporting files if progressive disclosure is needed), matching the 6-field spec.
2. A draft entry for `registry/skills.json` matching the fields in `registry/SCHEMA.md`, with `quality_score: null` and `security_audit.status: "pending"` — never self-set these fields as already passed.
3. If a candidate closely overlaps an existing skill in the registry (≥80% scope), report that instead of creating a parallel entry — dedup/novelty-check is step 8, which runs before this step starts producing new content.
