---
name: classroom-materials-builder
description: Validates the structural completeness of a student-facing classroom material record (in-class worksheet, take-home homework sheet with answer key, or classroom learning game) before it goes to students — every item has a task, every homework item's answer key covers every item with no gaps, worksheets are flagged if an item has no described response space, games are flagged if their rules are missing or don't reference the declared lesson topic — then renders it to clean Markdown. Use when checking a worksheet/homework sheet/game JSON record for shipping-safety gaps (an unanswered homework question, a task with no place for the student to respond, a game with no rules) before printing or handing it out. Do NOT use this to generate the actual tasks/questions/answers (no LLM/AI call, ever) — that stays a human/agent authoring job — and do NOT use it to judge whether the content is pedagogically good, factually correct, or age-appropriate; it checks structure only.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-26). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in 3 of prior system's real previously-deployed skills for K12 teachers (prior deployed system skills/classroom_worksheet, homework_sheet, learning_game) for the domain distinctions this validator encodes: classroom_worksheet's items are organized by lesson ACTIVITY (Khởi động/Hình thành kiến thức/Luyện tập/Vận dụng) and must each carry a described response space (dòng kẻ trống/bảng trống/sơ đồ trống) since the student fills it in during class, not just answer a bare question; homework_sheet's items are organized by difficulty/type (TN/TL, cơ bản→nâng cao) and its answer key must trace back to the question set with 'no thừa, no thiếu'; learning_game requires a complete rules/steps section tied to the lesson's actual knowledge content, not a generic entertainment activity, plus a question/task set with a matching answer set. prior system's own orchestration machinery for these 3 skills (persona/effort/token_budget tuning, imperative-ladder tool-call requirements, `use_skill`/`script_exec`/`llm_call`/`request_input` calls, Jinja2 profile placeholders, workspace-scan-before-work conventions, sub-agent dispatch for content generation) was NOT ported — none of that is domain knowledge, and this skill never calls an LLM/AI API of any kind. Per thatlq1812 direction (2026-07-26), consolidated 3 separate prior system skill folders into one, and — like `lesson-plan-builder` before it — deliberately excludes prior system's bureaucratic-paperwork skills from this tier."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["worksheet", "homework-sheet", "learning-game"]
---

# classroom-materials-builder

Validates the structural completeness of a student-facing classroom material — an in-class worksheet, a take-home homework sheet with an answer key, or a classroom learning game — before it reaches students, then renders it to clean Markdown.

## Why this skill, and why this scope

Consolidates 3 prior system skill folders that all produce **student-facing** materials a teacher hands out, as distinct from `lesson-plan-builder` (the teacher's own internal KHBD, never seen by students): `classroom_worksheet` (in-class, tied to that lesson's activities), `homework_sheet` (take-home, organized by difficulty/type, with an answer key), and `learning_game` (a classroom game/interactive activity tied to lesson content). prior system had these as 3 separate ~1.1.0 skill folders, each packed with harness-specific orchestration (persona/effort/token-budget tuning, imperative-ladder tool-call sequencing, `use_skill`/`script_exec`/`llm_call` dispatch, Jinja2 profile placeholders, workspace-scan conventions) — none of that is domain knowledge and none of it was ported.

**Be honest about scope**: unlike `lesson-plan-builder` (CV5512 has a legally mandated 4-activity structure) or `assessment-builder`/`competency-rubric-builder` (circular-mandated structures), these 3 prior system skills are light on hard regulatory structure and heavy on open-ended pedagogical content generation — game genre, worksheet task design, homework question phrasing are all free-form creative/pedagogical work with no fixed national format. What actually exists across all 3, checkable deterministically, is **shipping-safety structure**: does every item have a task, does every homework item have an answer, does every worksheet item have somewhere for the student to actually respond, does the game have rules that tie to the stated topic. This skill checks exactly that — nothing more. See "Known limitations" below for what it deliberately does not attempt to check.

## What this validator encodes (the real, checkable invariants)

- **Common to all 3 types**: `material_type` must be `worksheet`/`homework`/`game`; `subject`/`grade`/`topic` must be non-empty; `items` must be a non-empty list; every item must have a non-empty `task` (hard error — a blank task is not a real classroom material).
- **`worksheet`**: every item missing a `response_space` description is a **warning** — prior system's `classroom_worksheet` core distinction from a plain question sheet is that the student fills something in (a line, a table, a diagram) during class, not just answers a bare prompt.
- **`homework`**: every item missing a non-empty `answer` is a **hard error**, naming the exact item — an unanswered homework question shipped to students with no key is prior system's own stated failure mode ("đề rỗng"/no answer coverage). Every item missing a `difficulty` tag is a **warning** — homework is conventionally grouped by difficulty/type, but this is a softer signal than the answer-key gap.
- **`game`**: an empty/missing `rules` field is a **hard error** — a game with no rules is not playable. `rules` text not containing the declared `topic` string is a **warning** (literal substring check, same caveat as `lesson-plan-builder`'s competency cross-check) — a learning game that never mentions its own lesson topic may be a generic entertainment activity, not the tied-to-content activity prior system's own skill required. A missing/non-positive `estimated_duration_minutes` is also a **warning**.

## Run

```bash
python scripts/validate_material.py <material.json> [--render material.md] [--force]
```

Start from `assets/material_template.json`. Exit 0 = structurally valid (warnings may still print — read them, they're quality signals, not blockers), exit 1 = errors block (printed with item-level detail, e.g. `items[1] (id='2'): answer is required...`), exit 2 = malformed input or `--render` refusing to overwrite an existing file without `--force`. `--render` only writes output when there are zero errors.

## What this skill does NOT do

- Doesn't generate the actual pedagogical content — tasks, questions, hints, answers, game rules — at all. No LLM/AI call of any kind, ever. A human or an agent working with the teacher fills the JSON; this only checks it before it ships.
- Doesn't judge pedagogy quality, factual correctness, age-appropriateness, or whether a game is actually fun/playable — pure structural completeness.
- Doesn't check that a worksheet's tasks map to a lesson plan's actual activities, or that a homework set's difficulty distribution is balanced — those are the richer checks `classroom_worksheet`/`homework_sheet` describe as model judgment calls in prior system, not deterministic rules; manufacturing a fake rigorous check here would be dishonest about what's actually checkable.
- Doesn't produce a `.docx` in any particular font/margin convention — delegate that formatting step to `office-doc-creator` once the Markdown passes validation.
- Doesn't cover prior system's administrative-paperwork skill types — deliberately out of scope for this tier, per thatlq1812 direction (see `lesson-plan-builder/SKILL.md`).

## Verified

A valid worksheet, a valid homework sheet with a complete answer key, and a valid game all validated with zero errors and rendered correctly to Markdown (Vietnamese diacritics intact); a homework sheet with one item's answer left empty was correctly refused, naming the exact item (`items[1] (id='2')`); a game with no `rules` field was correctly refused; malformed JSON, missing required fields, and an invalid `material_type` were all correctly refused/rejected with exit codes 2/1/1; `--render` without `--force` onto an existing file correctly refused (exit 2), `--force` correctly overwrote; 3 soft-quality cases (worksheet item missing `response_space`, homework item missing `difficulty`, game `rules` not mentioning the declared `topic` + missing `estimated_duration_minutes`) all correctly warned at exit 0 without blocking.

## Known limitations (v0.1.0)

- **There isn't much hard structure here, and this is by design, not a gap to be filled later.** Compared to `lesson-plan-builder`, this skill checks far less because far less is actually mandated for these 3 material types — worksheet task design, homework question phrasing/difficulty balance, and game genre/rule complexity are all open-ended pedagogical judgment with no fixed national format to validate against. Over-engineering a fake-rigorous validator for content that has no real structural rules would produce false confidence, not safety.
- The `rules`-mentions-`topic` check is a literal, case-insensitive substring match, same limitation as `lesson-plan-builder`'s competency cross-check — a teacher who paraphrases the topic (uses a synonym or a narrower/broader phrase) gets a spurious warning. Read it as a prompt to double-check, not an infallible finding.
- The `difficulty` field on homework items is free-form text, not validated against a fixed vocabulary (unlike `lesson-plan-builder`'s fixed CT GDPT 2018 competency lists) — there is no fixed national difficulty taxonomy for a homework sheet to validate against, only convention (cơ bản/vận dụng/nâng cao is common but not mandated).
- No cross-check against an actual lesson plan (KHBD) — prior system's own skills describe reading a KHBD from the workspace to ground a worksheet's activities or a game's content, but that's workspace-scan orchestration infrastructure, not something a standalone JSON validator can check; a future version could add an optional KHBD-cross-reference field if real use shows the need.
- One combined template (`assets/material_template.json`) covers all 3 material types via the shared `material_type` discriminator, rather than 3 separate template files — fields irrelevant to a given type (e.g. `rules` for a worksheet) are simply left unused; the validator ignores fields that don't apply to the declared `material_type`.
