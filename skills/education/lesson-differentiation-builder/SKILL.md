---
name: lesson-differentiation-builder
description: Validates a K-12 lesson-differentiation JSON record -- an EXISTING lesson adapted into below/at/above grade-level proficiency tiers (Tomlinson framework) -- checking every tier's worksheet covers the exact same shared core task set (so tiers cannot drift onto different content, only differ in scaffolding or extension), that Below has at least one scaffold under a density cap, that Above has a genuine extension distinct from the core task, and fixed tier/group-label vocabulary -- then renders a teacher plan and three student tier worksheets to Markdown. Use when differentiating an existing lesson for students at different levels, or checking a drafted differentiation plan for structural gaps before handing out tiered worksheets. Do NOT use to create a new lesson from scratch (lesson-plan-builder's job) or to judge whether scaffolds/extension are pedagogically well-designed -- structure and cross-tier consistency only, never teaching quality.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, pathlib) -- no dependency, no venv needed, local-only, zero network calls. See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "github.com/anthropics/k12-teacher-skills, k12-lesson-differentiation skill, Apache-2.0, Anthropic + Learning Commons, a real deployed system in Claude for Teachers -- read directly (SKILL.md in full, plus references/math.md and references/output.md) for the actual domain knowledge kept here: the Tomlinson-framework below/at/above tier structure with fixed Group A/B/C labeling; the core structural discipline that everything shared across tiers (essential question, core task set, vocabulary, reflection prompt, anchor activity) must live ONCE so tiers cannot drift apart on WHAT students work on, only HOW; the Below-tier scaffold-with-a-density-cap rule (too many simultaneous supports is its own accessibility problem); the Above-tier requirement for a genuine qualitatively-different extension, never just more of the same; and the requirement that every tier's worksheet closes with the same open-ended reflective prompt. Deliberately NOT ported: the source's Learning Commons Knowledge Graph standards-grounding connector (Scriptorium has no such connector), its bash/Playwright DOCX render pipeline (out of scope -- delegate to office-doc-creator per this registry's convention), its state/jurisdiction standards-detection logic, its curriculum-name copyright guardrail (IM/OpenSciEd-specific), and its own harness-specific conversational-flow instructions (draft-offer wording, task-list announcements, chat-message closing script) -- none of that is domain knowledge portable to a standalone JSON validator. The single-source-of-truth 'shared' block is reimplemented here as an explicit reference-and-cross-check mechanism (worksheet_items reference shared.core_tasks by key, and the validator mechanically checks every tier covers the identical key set) rather than the source's own render-time substitution, since this skill has no render pipeline of its own to enforce it by construction."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["differentiation-plan", "worksheet"]
---

# lesson-differentiation-builder

Validates a K-12 lesson-differentiation record -- an existing lesson adapted into below/at/above grade-level proficiency tiers -- then renders a teacher-facing plan and three student-facing tier worksheets to Markdown. Catches cross-tier content drift and missing tier-specific requirements deterministically, before tiered materials reach students.

## Why this skill, and why this scope

Closes a real gap in this registry's Teacher tier (`docs/specs/STRATEGY_SPEC.md` §5.1): `lesson-plan-builder` builds/validates one lesson, `classroom-materials-builder` validates one worksheet/homework sheet/game, `assessment-builder` balances exams, `competency-rubric-builder` validates rubrics, `grading-and-feedback` scores and lints remarks -- none of them differentiate an existing lesson into leveled versions for students at different proficiency levels.

Elicited from `github.com/anthropics/k12-teacher-skills`'s `k12-lesson-differentiation` skill (Apache-2.0, co-developed by Anthropic and Learning Commons, a real production skill in "Claude for Teachers") -- read directly rather than guessed, per this project's real-elicitation-source requirement for the tier this skill actually sits at. This is a **general-capability** skill: the Tomlinson differentiation framework is publicly documented pedagogy, not a country-specific legal mandate, so it does not carry the CV5512/TT27/TT22 Vietnamese-regulation grounding `lesson-plan-builder`/`grading-and-feedback` do -- it uses plain English field names and is not tied to a specific national curriculum, unlike its sibling skills.

The source skill's own real orchestration machinery (a Learning Commons Knowledge Graph connector for standards grounding, a bash+Playwright DOCX render pipeline, state/jurisdiction detection, a curriculum-name copyright guardrail, and its own conversational-flow scripting) is infrastructure for Anthropic's own agent runtime and connector ecosystem, not domain knowledge -- none of it was ported. What was worth keeping, and is encoded here as a deterministic validator: the below/at/above tier structure with fixed Group A/B/C labeling, the single-shared-content discipline that prevents tiers from drifting onto different material, the Below-tier scaffold-density-cap rule, and the Above-tier genuine-extension requirement.

## What this validator encodes (the real, checkable invariants)

- **A `shared` block holds everything common to all tiers exactly once**: `essential_question`, `core_tasks` (the actual task/problem set), `vocabulary`, `reflect_prompt` (the closing reflection every tier's worksheet ends with), and an optional `anchor_activity` (early-finisher task). This is the single most important idea kept from the source skill: writing shared content once, not per tier, is what makes drift structurally harder in the first place.
- **Every tier's `worksheet_items` must reference the exact same set of `shared.core_tasks` keys** (`{"ref": "from_shared:<key>"}`) -- a hard error names any tier missing a reference or holding a stray/duplicate one. Tiers may differ in *how* a task is presented (`modification` text) but never in *which* tasks exist -- the mechanical stand-in for the source skill's render-time single-source enforcement (R6: same core tasks across tiers).
- **Fixed tier set and group-label vocabulary**: `tiers` must have exactly `below`/`at`/`above` (no 4th tier, no renaming); each tier's `group_label` must be exactly `Group A`/`Group B`/`Group C` respectively -- the same convention the source skill uses on student-facing documents.
- **Below tier**: `entry_point` (where these students start relative to the core task) and at least one non-empty `scaffolds` entry are required; more than 6 scaffolds is a warning (a density-cap guideline, not a hard cap -- too many simultaneous supports can be its own accessibility problem).
- **Above tier**: `entry_point` and a non-empty `extension` are required; an `extension` that is verbatim-identical to any shared core task is a warning (a genuine extension should be qualitatively different, not just a repeat).
- **At tier**: no hard requirements beyond covering the shared core tasks (it is the grade-level default); a non-empty `modification` on an At-tier worksheet item is a warning, since a real change there usually belongs on Below or Above instead.

## Run

```bash
python scripts/validate_differentiation.py <plan.json> [--render-plan plan.md] [--render-worksheets DIR] [--force]
```

Start from `assets/differentiation_template.json`. Exit 0 = structurally valid (warnings may still print -- read them, they're pedagogical quality signals), exit 1 = errors block (printed with field-level detail), exit 2 = malformed input or a render target already exists without `--force`. `--render-plan`/`--render-worksheets` only write output when there are zero errors; `--render-worksheets` writes `worksheet_below.md`, `worksheet_at.md`, `worksheet_above.md` into the given directory (created if missing).

## What this skill does NOT do

- Doesn't generate the differentiated content itself -- no LLM/AI call of any kind. The teacher (or the agent working with the teacher) writes the core tasks, scaffolds, and extension into the JSON; this only checks and renders it.
- Doesn't judge whether the scaffolds are actually appropriate for a named learner need, whether the extension is genuinely rigorous, or whether the entry points are well-calibrated -- pure structural/cross-reference validation, same stance as every sibling Teacher-tier validator in this registry.
- Doesn't ground standards/curriculum via any knowledge-graph connector (the source skill's Learning Commons KG integration was deliberately not ported -- Scriptorium has no such connector and never adds an AI backend per `CLAUDE.md` principle 8). The optional `standard` field is free text, unvalidated.
- Doesn't produce a `.docx`/print-ready document -- delegate that formatting step to `office-doc-creator` once the rendered Markdown passes validation, matching the delegation pattern every sibling Teacher-tier skill uses.
- Doesn't create a new lesson from scratch -- this adapts a lesson the teacher already has (captured in `source_lesson_summary`); a request for a brand-new leveled lesson is `lesson-plan-builder`'s job.
- Doesn't check that `source_lesson_summary` accurately describes a real lesson, or that `core_tasks` are factually/mathematically correct -- content accuracy is out of scope, same structural-only stance as `lesson-plan-builder`.

## Chains into `lesson-plan-builder`

When the source lesson being differentiated doesn't exist yet as a structured record, build it first with `lesson-plan-builder` (`skills/education/lesson-plan-builder/`), then summarize its `ten_bai`/`muc_tieu.kien_thuc` into this skill's `source_lesson_summary` field before differentiating. This chain is real but not forced: differentiation commonly starts from a lesson that already exists outside Scriptorium's own JSON records (a textbook lesson, a lesson a teacher already taught), which is exactly this skill's scope -- `source_lesson_summary` accepts a free-text description either way.

## Verified

A valid Grade 6 math ratios plan (2 shared core tasks, distinct genuine scaffolds/extension) validated with zero errors and rendered correctly to a teacher plan plus 3 tier worksheets, confirming worksheet content stays literally identical to the shared core tasks across tiers while modification/scaffold/extension text correctly differs per tier. `--render-plan`/`--render-worksheets` correctly refused to overwrite existing output without `--force` (exit 2) and correctly overwrote with it. A deliberately broken fixture (empty `essential_question`, a duplicate `core_tasks` key, an empty core-task `task`, a missing `above` tier alongside an unrecognized `advanced` tier, a wrong `group_label`, an empty `below.scaffolds` list, a malformed `ref` missing the `from_shared:` prefix, and a Below-tier worksheet consequently missing both core-task references) was correctly caught as 9 distinct named errors (exit 1), alongside 1 correctly non-blocking warning (an At-tier item carrying a modification). A separate fixture confirmed the two remaining warning paths: 7 Below-tier scaffolds (over the 6-entry density-cap guideline) and an Above-tier `extension` verbatim-identical to a shared core task, both warned without blocking (exit 0). Malformed JSON, a top-level JSON array, and an empty object (all 6 required top-level fields reported missing) were all correctly refused/rejected (exit 2/2/1). The bundled `assets/differentiation_template.json` itself validates cleanly (exit 0), matching every sibling Teacher-tier skill's convention of a structurally-valid starting template.

## Known limitations (v0.1.0)

- The "same core task set across tiers" check is a reference-key match, not a content-equality check on the task text itself -- since the task text lives once in `shared.core_tasks` and tiers only ever reference it by key, there is no field where a tier could retype (and thus drift) the task text even if it wanted to; this is enforced by the schema shape itself, not an additional runtime check.
- The Above-tier "genuine extension" check is a literal, case-insensitive string-equality comparison against each shared core task -- a paraphrased near-duplicate extension (same task, reworded) will not be flagged. Same limitation class as `lesson-plan-builder`'s competency cross-check and `classroom-materials-builder`'s topic-mention check.
- No Learning Commons Knowledge Graph (or any other) standards-grounding connector -- `standard` is free text, never verified against an official framework. A teacher/agent citing a standard is trusted, not checked.
- No support for a 4th/intervention tier, an ELL-specific WIDA-banded layer, or IEP-goal-specific scaffold tagging (all real follow-ups the source skill itself offers as next-step options) -- v0.1.0 covers the classic 3-tier (below/at/above) case only.
- `learner_needs` is accepted and rendered into the teacher plan if present, but never validated or cross-checked against the Below tier's actual scaffolds -- a teacher could note a real learner need and still write scaffolds that don't address it; that judgment call stays human/agent, not mechanically checkable.
- Unlike `lesson-plan-builder`'s CV5512 grounding, this skill is not tied to any specific national curriculum or regulation -- `subject`/`grade`/`topic`/`standard` are all free text, so it works equally for a US Common Core lesson or a Vietnamese CT GDPT 2018 lesson, but validates no framework-specific vocabulary either way.
