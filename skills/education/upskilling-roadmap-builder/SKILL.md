---
name: upskilling-roadmap-builder
description: Computes the gap between a caller-declared list of current skills and a caller-declared list of target-role skills, then sequences the missing skills into a day-by-day study/review roadmap using the same interleaved round-robin-new-skills + periodic-review-everyone-so-far scheduling core as study-plan-builder (imported directly, not reimplemented). `scripts/from_gap_analysis.py` converts a `knowledge-gap-analyzer` report directly into this skill's input, chaining the two into one real pipeline (confidence-scored diagnostic becomes an actionable schedule). Use when a professional wants a concrete schedule for closing a skill gap toward a target role over N days, given skill lists they (or another tool, or knowledge-gap-analyzer) already supplied. Do NOT use this to decide what skills a role actually requires or what skills the learner actually has -- both lists are always caller-supplied input, never invented, researched, or inferred by this skill.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, local-only, zero network calls. Requires skills/education/study-plan-builder/scripts/build_study_plan.py to be present as a sibling skill in the same skills/ directory (imported directly for its scheduling core). Verified running clean: Claude Code (2026-07-29).'
metadata:
  domain: education
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Lifelong Learner / Upskilling Professional role-capability tier (general-capability, public-source grounding per CLAUDE.md principle 4). Gap-analysis-then-sequence shape grounded in standard career-development practice: skills-gap analysis is a documented technique in competency-based HR/L&D frameworks (e.g. SHRM competency modeling, O*NET's skills-by-occupation database structure comparing a worker's current skill profile against an occupation's required skill profile). The scheduling core itself is NOT reinvented here -- it is imported directly from skills/education/study-plan-builder/scripts/build_study_plan.py (that skill's own interleaved-new-topics + periodic-review round-robin algorithm, original to that skill's session per its own SKILL.md), so this skill inherits that algorithm's grounding rather than duplicating or re-deriving it."
  version: 0.2.0
  changelog_0_2_0: "Added scripts/from_gap_analysis.py: converts a knowledge-gap-analyzer JSON report directly into this skill's own input shape, chaining the two skills into one real pipeline (diagnostic report -> actionable schedule) instead of leaving them as two disconnected tools with overlapping gap-computation logic. Resolves docs/DECISIONS_PENDING.md's registry-review item 8 (thatlq1812-flagged overlap between the two skills) by composing them rather than merging or deleting either -- they serve genuinely different jobs (confidence-scored diagnostic vs. binary-gap schedule)."
  grounding: not_applicable
  object_type: ["skills-gap", "roadmap"]
---

# upskilling-roadmap-builder

Turns a caller-declared skill gap (target-role skills minus current skills) into a day-by-day study/review roadmap. Gap computation is new; the scheduling itself is study-plan-builder's own algorithm, reused by direct import, not reimplemented.

## Why this skill, and why this scope

This is for the **Lifelong Learner / Upskilling Professional** role-capability tier. Unlike the K12 Student tier that `study-plan-builder` was built for, this is a general-capability skill: skills-gap analysis (compare a worker's current competencies against a target role's required competencies, sequence the gap) is publicly documented, well-established career-development practice, so it needs no expert elicitation interview per CLAUDE.md principle 4's "general-capability" tier.

The scheduling problem this skill needs to solve after computing the gap -- spread out new items, don't repeat one back-to-back, periodically review everything introduced so far -- is the exact same problem `study-plan-builder` already solved. Reinventing that algorithm here would violate CLAUDE.md's "before starting a new skill, query the registry ... if an existing skill already covers scope, extend/version it instead of creating a parallel entry" instruction, applied to logic reuse specifically: this skill imports `build_study_plan.interleave_new_sessions` / `build_study_plan.build_schedule` / `build_study_plan.PlanError` directly (see `scripts/build_roadmap.py`'s `_import_scheduling_core()`), rather than copy-pasting or re-deriving the round-robin+review logic. `skills/education/study-plan-builder/` itself is never modified -- this is a one-directional dependency, resolved relative to this script's own path so it works regardless of caller cwd.

## Relationship to `knowledge-gap-analyzer` (2026-07-29 clarification — `docs/DECISIONS_PENDING.md` resolved item 8)

Both skills compute a gap between what a learner has and a target role needs — this is a deliberate, documented overlap, not an accidental duplicate. They serve different jobs: `knowledge-gap-analyzer` is a **diagnostic** (confidence-scored: "which skills am I below-bar on, exactly") that produces a report, never a schedule. This skill is **actionable**: given a gap (binary held/not-held), it produces a real day-by-day schedule. Chain them for real:

```bash
python skills/education/knowledge-gap-analyzer/scripts/analyze_knowledge_gap.py <self_assessment.json> <target_requirements.json> --threshold N --json > gap_report.json
python scripts/from_gap_analysis.py gap_report.json --weight N -o skills_gap.json
python scripts/build_roadmap.py skills_gap.json --days N
```

`from_gap_analysis.py` never invents a per-skill weight from the confidence numbers (turning "confidence 1 vs 2" into a formula-derived weight would be exactly the invented-methodology `knowledge-gap-analyzer` itself refuses to do) — every gap skill gets the same caller-declared `--weight`. Exit 1 (not an error) if the report already shows `ready: true` — nothing to schedule.

## Run

```bash
python scripts/build_roadmap.py <skills_gap.json> --days N [--sessions-per-day K] [--review-every M] [--output roadmap.md] [--json]
```

Start from `assets/skills_gap_template.json`: `target_role` (string), `current_skills` (list of skill-name strings the learner already has), `target_skills` (list of `{name, weight}` -- everything the target role needs, `weight` 1-5 default 2, same semantics as study-plan-builder's topic weight). The gap is every `target_skills` entry whose name doesn't case-insensitively match a `current_skills` entry; only the gap gets scheduled. If the gap is empty, the script reports so explicitly (exit 0) and produces no schedule -- it never emits an empty/meaningless plan.

`--review-every` must be ≥2. Output is a Markdown table + day-grouped checklist plus a gap/already-held summary by default; `--json` prints the raw gap + schedule instead.

Exit codes: 0 = roadmap generated (or gap already empty), 1 = well-formed input but not enough schedule capacity for the computed gap (a validation failure, same message shape as study-plan-builder's own capacity refusal), 2 = malformed input (bad JSON, missing/invalid fields, duplicate skill name, out-of-range weight, invalid `--days`/`--sessions-per-day`/`--review-every`, or the study-plan-builder scheduling core can't be found at its expected sibling path).

## What this skill does NOT do

- Doesn't decide what skills a target role actually requires, or what skills the learner actually has -- both `current_skills` and `target_skills` are always caller-supplied; this skill never researches a role's real skill requirements or infers a learner's competence.
- Doesn't do fuzzy/semantic skill-name matching when computing the gap -- matching is exact (case-insensitive, whitespace-trimmed) string equality, same "never guess a match" discipline as `personal-profile-manager`'s `autofill.py`. A learner's "SQL" vs a target list's "Structured Query Language" will NOT be recognized as the same skill; the caller must normalize naming before use.
- Doesn't reimplement or fork study-plan-builder's scheduling algorithm -- it imports it. If study-plan-builder's algorithm changes in a future version, this skill's roadmaps change with it automatically (a deliberate, documented coupling, not an accident).
- Doesn't adapt the roadmap based on how well a study session actually went -- same fixed, deterministic, non-adaptive schedule as study-plan-builder (inherits that skill's own documented limitation).
- Doesn't call any LLM/AI API -- pure stdlib arithmetic plus JSON I/O.

## Verified

Real 5-skill gap (2 of 5 target skills already held) over 14 days, `--sessions-per-day 1`, default `--review-every 4`: gap correctly computed to the 3 missing skills, schedule produced with no back-to-back repeats and periodic review, `already_held` correctly listed and excluded. Empty-gap case (all target skills already held) correctly reported "OK: no skill gap" with exit 0 and no schedule. Insufficient-capacity case (`--days 1`, large gap) correctly refused with exit 1 and an actionable "add N more days" message identical in shape to study-plan-builder's own. Malformed-input cases all correctly refused with exit 2: missing `target_role`, `current_skills` containing a non-string entry, duplicate `target_skills` name (case-insensitive), out-of-range weight (0 and 6), `--review-every 1`, `--days 0`. `--json` output verified to contain `target_role`, `current_skills`, `already_held`, `gap`, and `schedule` keys with correct values. Verified the import of `study-plan-builder`'s functions resolves correctly from this skill's own script path regardless of invocation cwd (ran from repo root and from inside `skills/education/upskilling-roadmap-builder/`). **`from_gap_analysis.py` (2026-07-29) verified real end-to-end**: a real `knowledge-gap-analyzer` run (3 assessed skills, 1 below threshold + 1 never-assessed against a 4-skill target role) piped into `from_gap_analysis.py --weight 3` correctly produced a `skills_gap.json` with the 2 already-met skills as `current_skills` and all 4 target skills declared (the 2 gap skills at the given weight) — fed directly into `build_roadmap.py --days 10`, which correctly scheduled only the 2 real gap skills (SQL, Kubernetes), excluding the 2 already-held ones. A `ready: true` report correctly refused conversion (exit 1, "nothing to schedule"); a malformed report missing required keys, an out-of-range `--weight`, and an existing output without `--force` were each correctly refused (exit 2).

## Known limitations (v0.1.0)

- Gap matching is exact string match only (see above) -- no synonym/alias table for skill names that mean the same thing under different labels.
- Inherits every documented limitation of `study-plan-builder`'s scheduling core (no true per-topic spaced-repetition intervals, no mastery-based adaptation, opaque session-length unit) since the scheduling logic is directly imported from it, not reimplemented.
- Hard-coupled to `study-plan-builder`'s file layout (`skills/education/study-plan-builder/scripts/build_study_plan.py` relative to this skill's own script path) -- if that skill is ever renamed, moved, or removed, this skill breaks with an explicit exit-2 error naming the expected path, rather than failing silently.
- No notion of skill prerequisites/ordering within the gap beyond weight -- e.g. it won't automatically schedule "SQL basics" before "advanced SQL" unless the caller's `target_skills` list is itself already ordered/weighted to reflect that.
