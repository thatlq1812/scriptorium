---
name: group-work-coordinator
description: Validates a caller-declared RACI matrix (Responsible/Accountable/Consulted/Informed) for a group project's task list — checks every task has exactly one Accountable person, every person named in the matrix is a declared group member (no phantom assignees), and no task is orphaned (assigned to nobody); warns (non-blocking) on a task with no Responsible person and on a declared member who never appears in any task. Renders a validated matrix to a clean Markdown table. Use when assigning or reviewing who owns what on a group project before work starts, to catch an unowned task or a double-accountable task early. Do NOT use this to decide WHO should be assigned to what — task assignment is a group decision this skill never makes; it only checks that a matrix the group already agreed on is structurally sound.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.
metadata:
  domain: general
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "General-capability tier per CLAUDE.md principle 4 — public-source grounding, no expert interview needed. RACI (Responsible/Accountable/Consulted/Informed) is a standard, widely-taught project-management responsibility-assignment convention (documented across public project-management references, e.g. PMI/PMBOK-adjacent materials and university project-management course guidance on responsibility assignment matrices), not a niche or tacit practice. The specific invariants encoded here — exactly one Accountable per task (the single most consistently taught RACI rule, since more than one Accountable defeats the point of the model), every named person must be a real team member, and no task should go unassigned — are the standard textbook RACI rules, not an invented interpretation. Scoped as a pure structural validator, matching this repo's own competency-rubric-builder/assessment-builder posture: the group decides the actual assignments, this only checks the resulting matrix is internally consistent. domain deliberately stays 'general' (not 'education') even though this skill's audience-tier home is University Student -- RACI matrices are a genuinely domain-agnostic project-coordination convention (any team, any industry), not an education-specific artifact, matching CLAUDE.md's own definition of the 'general' domain tag (2026-07-29 registry domain-consistency review, docs/DECISIONS_PENDING.md)."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["raci-matrix", "group-project"]
---

# group-work-coordinator

Validates a RACI (Responsible/Accountable/Consulted/Informed) matrix for a group project's task list, then renders it to a clean Markdown table. Catches an unassigned task, a task with zero or multiple Accountable owners, or a matrix entry naming someone who isn't actually on the team, deterministically, before the group starts work under a broken assignment.

## Why this skill, and why this scope

RACI is standard, publicly-documented project-management practice for assigning responsibility across a team, not a niche or tacit process — general-capability tier per CLAUDE.md principle 4. The rule this skill enforces hardest — **exactly one Accountable person per task** — is the single most consistently taught RACI invariant: Accountable means "the buck stops here," and naming zero or multiple Accountable people for the same task defeats the entire purpose of the model (nobody is answerable, or everybody can blame someone else). The other two invariants — every named person must be a declared group member, and no task may go unassigned — are basic data-integrity checks a group project doing this by hand (a shared spreadsheet, a Notion table) has no mechanical guard against, and both are cheap to catch here before the group commits to the plan.

Same posture as `competency-rubric-builder`/`assessment-builder` in this repo: this skill never decides WHO should do WHAT — that's the group's own negotiation — it only validates that whatever the group already agreed on is internally consistent.

## What a structurally sound RACI matrix requires (the domain knowledge this validator encodes)

- **A declared member list**: `members`, a non-empty list of distinct, non-empty names.
- **A non-empty task list**, each task with:
  - `task_name` — non-empty string, distinct across all tasks.
  - `raci` — a non-empty object mapping a member name to exactly one of `"R"`, `"A"`, `"C"`, `"I"`. An empty `raci` object (no one assigned) is an **orphan task**, a hard error.
- **Exactly one Accountable (`"A"`) per task** — zero is an unowned task, more than one defeats the "buck stops here" purpose of the model.
- **Every person named in any task's `raci` must be in the declared `members` list** — a matrix entry naming someone not on the team is a hard error (catches a typo'd name or someone who was never actually added to the group).

Two additional checks are warnings, not hard errors, since both are legitimate in some real project shapes:

- A task with no Responsible (`"R"`) person — sometimes intentional if the Accountable person also does the work without a separate `R` entry, but worth a second look.
- A declared member who never appears in any task's `raci` — sometimes intentional (a member added to the roster but not yet assigned), but worth a second look.

## Run

```bash
python scripts/validate_raci_matrix.py <matrix.json> [--render matrix.md] [--force]
```

Start from `assets/raci_matrix_template.json` (a valid, warning-free 4-member/4-task example for a marketing research group project — read it for the exact JSON shape). Exit 0 = structurally valid (warnings may still print — read them, they flag a task with no Responsible person or a member never assigned anywhere), exit 1 = errors block (printed with field-level detail: exact task index/name and the exact person/letter involved), exit 2 = malformed input, or `--render` target already exists without `--force`. `--render` only writes output when there are zero errors.

## What this skill does NOT do

- Doesn't decide who should be Responsible/Accountable/Consulted/Informed for any task — that assignment is always the group's own decision, supplied as input; this only checks the result is internally consistent.
- Doesn't judge whether the workload is balanced, whether the right person is Accountable for the right task, or whether the task breakdown itself makes sense — pure structural validation (member existence, exactly-one-Accountable, no orphans), never a judgment about the plan's quality.
- Doesn't track actual task progress/completion status — this validates the assignment matrix at planning time, not a live project-tracking board.
- Doesn't call any LLM/AI API — pure stdlib structural checking, no network calls of any kind.
- Doesn't produce a final formatted document — delegate to `office-doc-creator` once the matrix passes validation, if a polished deliverable is needed.

## Verified

`validate_raci_matrix.py`: the bundled `assets/raci_matrix_template.json` (4 members, 4 tasks, each with exactly one Accountable and at least one Responsible) validated with **zero errors and zero warnings**, and `--render` produced a correct Markdown RACI table. A matrix with 5 tasks covering every failure mode in one file — a task with no Accountable, a task with two Accountable people, a task naming a phantom member ("Eve") not in the declared roster, a fully orphaned task (empty `raci`), and a task using an invalid RACI letter ("X") — was correctly refused, naming all 5 errors exactly by task and detail (exit 1), with 3 correctly-triggered no-Responsible warnings printed alongside. An empty `members` list combined with an empty `tasks` list was correctly refused (exit 1, first error reported before the code path that would also flag the empty task list). A duplicate member name ("Alice" listed twice) and a duplicate `task_name` across two tasks were both correctly refused in the same run (exit 1, both named). Malformed JSON was correctly refused (exit 2, exact parse error reported).

## Known limitations (v0.1.0)

- No workload-balance check — a matrix where one member is Accountable for every task and another appears nowhere passes validation cleanly (the uninvolved-member warning fires, but it's a warning, not a block); balance is a group judgment call, deliberately not automated here.
- No task-dependency or ordering model — tasks are validated independently; whether task B can start before task A finishes is out of scope.
- The no-Responsible-person warning doesn't distinguish "Accountable person is also doing the work" (often fine) from "genuinely nobody is doing this task" (a real gap) — both look identical to this check, review manually.
- Doesn't validate task descriptions, deadlines, or deliverables — only the RACI assignment structure itself. A richer group-project-planning schema (deadlines, dependencies, deliverable format) is a possible v2+ extension if real use shows the need.
