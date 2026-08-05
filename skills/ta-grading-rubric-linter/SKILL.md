---
name: ta-grading-rubric-linter
description: Validates a TA's rubric-based grading run for one class against a rubric definition — every criterion score is checked against its declared max (a score exceeding its max is refused outright, never silently clamped, same discipline as grading-and-feedback's own per-criterion capping rule), rubric criteria weights are checked to sum exactly to the declared total, and a statistics pass (stdlib `statistics` only) flags cross-student consistency patterns worth a human double-check — a criterion scored for only one student out of many, a per-criterion Tukey 1.5×IQR outlier, or a student whose score is identical across every criterion (flatline) while the class otherwise shows variance. Use after a TA finishes grading a batch of students with one rubric, before scores are finalized/returned. Do NOT use this to judge whether a score is pedagogically correct, to grade content itself, or to compute a term/course grade across multiple assignments — it only checks internal consistency of one already-graded rubric run.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, statistics, collections) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Two grounded pieces of public/in-repo knowledge, no fabricated interview. (1) The per-criterion max-cap hard-refusal rule is deliberately REUSED, not re-derived, from this repo's own skills/grading-and-feedback/scripts/grade_exam.py, which already encodes the discipline that an essay/rubric criterion score exceeding its declared max_points is refused outright, never silently clamped -- applied here to a TA's multi-student rubric-grading run instead of a single teacher's one-exam grading. (2) The statistical outlier layer is grounded in two publicly documented conventions, not invented thresholds: the isolated-criterion-usage and flatline-score checks follow the general rubric-grading calibration/norming practice described in Stevens & Levi, 'Introduction to Rubrics: A Practical Guide to Creating and Using Rubrics for Assessment Program Effectiveness' (2013) and widely-published university teaching-center rubric-calibration/norming guides, which recommend spot-checking for graders/scores showing no discrimination across criteria or isolated/inconsistent criterion use; the per-criterion outlier fence uses the standard box-plot 1.5xIQR convention from John W. Tukey, 'Exploratory Data Analysis' (1977), also documented at NIST/SEMATECH e-Handbook of Statistical Methods S7.1.6 (https://www.itl.nist.gov/div898/handbook/prc/section1/prc16.htm) -- a citable, off-the-shelf statistic, not a self-invented threshold."
  version: 0.1.0
  grounding: required
  object_type: ["gradebook", "rubric"]
---

# ta-grading-rubric-linter

Validates a TA's rubric-based grading run for internal consistency: no criterion score ever exceeds its declared max (hard refused, never clamped), rubric weights sum correctly, and a stdlib statistics pass flags cross-student patterns worth a second look before scores are finalized.

## Why this skill, and why this scope

A single-course TA regularly grades a stack of students against one shared rubric — problem sets, lab reports, short-answer exams. The two failure modes that matter most are the same ones `grading-and-feedback` already guards against for a teacher's one-exam grading (a criterion score silently exceeding its own max), plus one TA-specific addition this skill adds: with N students graded against the same rubric, cross-student comparison becomes possible and cheap, so a script can flag statistically unusual patterns — an isolated criterion use, an outlier score, or a suspiciously flat score profile — that are worth a human double-check before grades go out, without ever judging whether a given score is *correct*.

The per-criterion max-cap rule is deliberately reused from `grading-and-feedback`'s `grade_exam.py`, not re-derived — same discipline, same hard-refusal shape, now applied to a multi-student TA grading run instead of one teacher's one-exam grading. The statistical layer is new to this skill and is grounded in two publicly documented conventions (rubric-calibration/norming literature, and Tukey's 1.5×IQR box-plot fence) — see `metadata.elicited_from` for exact citations. No threshold in this skill was invented without a citable source.

## What domain knowledge this skill encodes

- **A criterion score must never exceed its declared `max_points`.** Refused outright with the exact score/max shown — never silently clamped or accepted. Same rule as `grading-and-feedback`.
- **Rubric criteria weights must sum exactly to the declared `total_points`.** Off by even a fraction is refused, with the actual sum and shortfall/excess shown.
- **Cross-student statistical consistency is a warning layer, not a hard error** — a script cannot know whether an outlier score is a genuine top/bottom performer or a grading slip, so these are printed as flags for a human to review, never blocking:
  - a criterion scored for exactly 1 student out of N≥3 — isolated usage, possibly a rubric-version mismatch or data-entry slip.
  - a per-criterion Tukey 1.5×IQR outlier (needs ≥4 scored students on that criterion for quartiles to be meaningful).
  - a student with an identical score across every criterion they were graded on (≥3 criteria, zero variance) while the class shows real variance on those same criteria — a "flatline" pattern.

## Run

### 1. Validate the rubric definition

```bash
python scripts/validate_rubric.py <rubric.json>
```

Start from `assets/rubric_template.json`. Checks every criterion has a positive `max_points`, criterion names are unique, and the sum of all `max_points` equals the declared `total_points`. Exit 0 = structurally valid, exit 1 = errors (each named with exact numbers), exit 2 = malformed input.

### 2. Lint a grading run against the (already-validated) rubric

```bash
python scripts/lint_grading_run.py <rubric.json> <grading_run.json>
```

Start from `assets/grading_run_template.json`. Hard errors (exit 1, block, nothing is ever clamped): a score for a criterion not declared in the rubric, a score exceeding its criterion's max, a negative score, a duplicate `student_id`, a student with an empty `scores` object. Warnings (printed, exit 0, do not block): isolated-criterion-usage, Tukey-IQR outliers, flatline score patterns — see above. Exit 2 = malformed input.

## What this skill does NOT do

- Does not judge whether a score is pedagogically correct or whether a flagged outlier/flatline pattern is actually a grading error — it only surfaces statistically unusual patterns for a human to review. A legitimate top or bottom performer will still trigger the outlier warning; that is expected, not a bug.
- Does not compute a term/course grade across multiple assignments — that's a gradebook-level concern, out of scope here (same boundary `grading-and-feedback` draws against `grade-book-builder`).
- Does not grade essay/rubric content itself, and never calls an LLM/AI API — scores must already be assigned by the TA before either script runs; both scripts only validate/aggregate numbers already present in the input.
- Does not require every student to be scored on every declared criterion (partial/optional criterion use is allowed structurally) — but an unknown criterion name (not declared in the rubric at all) is always a hard error, never treated as a new/optional criterion.

## Verified

`validate_rubric.py`: the bundled 3-criteria template (6+2+2=10) passed clean; a weight-sum mismatch (8 vs declared 10) correctly refused showing the exact -2.0 shortfall; a rubric with a duplicate criterion name and a negative `max_points` correctly refused both issues in one run; malformed (non-JSON) input correctly refused with exit 2.

`lint_grading_run.py` against the bundled rubric (correctness/6, code_style/2, test_coverage/2): the bundled 3-student template graded clean with zero warnings; a score of 7 on a max-6 criterion correctly refused ("refused, never clamped"), exit 1; an unknown criterion name (`bonus_effort`) correctly refused; a negative score and a duplicate `student_id` in the same run correctly refused both issues; a student with an empty `scores` object correctly refused; malformed (non-JSON) grading-run input correctly refused with exit 2. Statistics layer: a 4-student run where one student was the only one scored on `test_coverage` correctly warned "isolated usage" AND separately flagged two Tukey-IQR outliers on `correctness`/`code_style` from the resulting 3-vs-1 split, exit 0 (warnings, not errors); a 6-student run with one student scoring an identical 2/2/2 across all three criteria while the class showed real variance on each criterion correctly warned "flatline pattern," exit 0.

## Known limitations (v0.1.0)

- The Tukey-IQR check only runs when a criterion has ≥4 scored students (fewer points make quartiles unstable/meaningless) — a small class or a rarely-used criterion gets no outlier check, by design rather than by a lowered threshold.
- All statistical warnings are heuristics computed from the numbers alone — they carry zero information about *why* a pattern exists (rubric drift, grading fatigue, a genuinely deserving score, a copy-paste error). A human must always interpret the flag; this script never auto-corrects or drops a flagged score.
- The flatline check only fires when a student was scored on ≥3 criteria; a rubric with fewer than 3 criteria total can never trigger it.
- No cross-run history — each invocation only sees one grading run in isolation; it cannot detect drift across multiple grading sessions for the same rubric (e.g. a TA getting stricter over the week).
