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
  version: 0.3.1
  changelog_0_3_1: "Added scripts/validate_skill.py: a mechanical validator for the 6-field spec + Scriptorium's required metadata fields (name==folder, description/compatibility length caps, elicited_from non-empty, risk_tier/task_type/source enum checks), stdlib-only. Closes a gap found comparing against github.com/anthropics/skills' skill-creator/scripts/quick_validate.py during this session's core-skill-package research round: this skill's own SKILL.md documented these structural constraints in prose but had no script gating them, relying entirely on an agent reading carefully. Running it retroactively against the full registry found 19 pre-existing real violations (compatibility field verification narrative accumulated past the 500-char cap over many sessions) -- all fixed the same session (moved to a 'Verified' section in each skill's own body)."
  adapted_from: "The 'pushy description' pattern + trigger eval set adapted from github.com/anthropics/skills skills/skill-creator (Apache-2.0), cleared via skills/license-compliance-check on 2026-07-26. The gold-template + scaffold-script pattern adapted from D:/elix/edustation/skills/_templates/ (owner's prior project) -- kept the copy-a-skeleton principle and REQUIRED/CHOOSE comment legend, dropped the harness-specific tier/CI-enforcement machinery. validate_skill.py (v0.3.1) adapted from the same anthropics/skills skill-creator's quick_validate.py -- pattern/structure only (allowed-keys check, name/folder match), rewritten from scratch in Scriptorium's own field set, no code copied verbatim. Rewritten in Scriptorium's own language/conventions throughout, not copied verbatim."
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

## What skill-creator does NOT do

- Doesn't grade the quality of the skill it just created — that's step 4 (quality evaluation loop), run separately, on ≥2 verified harnesses.
- Doesn't audit the security of the skill it just created — that's step 5 (security audit), a separate pipeline stage, never merged with step 4 (`docs/specs/STRATEGY_SPEC.md` §7 point 2).
- Doesn't decide on its own that a skill is "ready to use" — that status is only set when `registry/skills.json` has a non-null `quality_score` AND `security_audit.status = "passed"`.

## skill-creator's output

1. A `skills/<name>/SKILL.md` folder (plus supporting files if progressive disclosure is needed), matching the 6-field spec.
2. A draft entry for `registry/skills.json` matching the fields in `registry/SCHEMA.md`, with `quality_score: null` and `security_audit.status: "pending"` — never self-set these fields as already passed.
3. If a candidate closely overlaps an existing skill in the registry (≥80% scope), report that instead of creating a parallel entry — dedup/novelty-check is step 8, which runs before this step starts producing new content.
