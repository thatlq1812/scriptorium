---
name: student-progress-tracker
description: Deterministic aggregator/validator for a parent/guardian tracking a child's report-card/progress data across multiple periods over time -- validates structural completeness of a multi-period record (unique caller-declared period order, subject scores on the 0-10 scale, valid dates), then computes a plain arithmetic trend (per-subject and overall score deltas between consecutive periods, direction up/down/flat). Use when a parent has already-recorded scores from 2 or more report periods and wants a structural check plus a mechanical trend summary. Do NOT use this to grade or score any individual assessment (that's grading-and-feedback), and do NOT use it as a source of official weighting/classification logic -- like grade-book-builder, it never invents an official average; a caller-supplied reported_overall_average is used as-is, and if omitted this only computes a plainly-labeled unweighted mean, never presented as an official TBM.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, re, argparse) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "General-capability tier per CLAUDE.md principle 4 -- no expert interview needed; this is a mechanical restructuring of a task shape already elicited and shipped in skills/education/grade-book-builder/SKILL.md (grounded in prior system's real previously-deployed grade_book skill). grade-book-builder aggregates ACROSS assessment categories within a single term (weighted TBM); this skill aggregates the same kind of already-scored data ACROSS terms/periods over time for a parent audience instead of a teacher audience -- same domain object (0-10 Vietnamese numeric scale, already documented and reused verbatim from grade-book-builder, not a new invented meaning), different axis of aggregation (time, not category-weight), different audience (parent tracking their own child longitudinally, not a teacher computing a class-wide term rollup). The one hard caveat grade-book-builder documents -- never assert an official weighting/classification number without a real cited source -- is carried forward identically here: this skill computes a plain unweighted mean labeled 'computed_unweighted_average' only when no caller-supplied 'reported_overall_average' is given, and never invents a significance threshold for what counts as a 'meaningful' trend change -- every delta is a bare arithmetic difference, direction is strictly sign-based (up/down/flat), with no invented cutoff for how large a change must be to matter."
  version: 0.1.0
  grounding: required
  object_type: ["progress-record", "report-card"]
---

# student-progress-tracker

Validates a multi-period student progress record (report-card scores collected over 2+ terms/periods) for structural completeness, then computes a deterministic, plainly-labeled trend: per-subject and overall score deltas between chronologically consecutive periods, with a strict sign-based direction (up/down/flat). Renders a Markdown summary table alongside the JSON result.

## Why this skill, and why this scope

`grade-book-builder` already covers the teacher-side aggregation task -- combining multiple assessment scores WITHIN one term into a weighted class gradebook. This skill covers a genuinely different aggregation axis for the Parent/Guardian tier: combining a child's already-recorded scores ACROSS terms/periods, over time, to see whether they're trending up, down, or flat -- a parent's actual longitudinal question ("is my child improving in Math this year"), not a class-wide term rollup. The domain object (0-10 numeric scale) and the no-invented-official-numbers discipline are both carried over unchanged from `grade-book-builder`; only the aggregation axis and audience differ, which is why this is a separate skill rather than an extension of that one (a `--mode over-time` flag on `grade-book-builder` would conflate two genuinely different data shapes -- students-x-categories-within-a-term vs. periods-x-subjects-over-time -- into one script).

## The one hard caveat: no invented official average, no invented "significant change" threshold

Same discipline as `grade-book-builder`'s own documented caveat, applied to a different axis:

- **`reported_overall_average`** is always optional, caller-supplied. If the parent has the child's actual official term average from a real report card, it goes here and is used as-is, source-tagged `"reported"` in the output.
- If omitted, this script computes a **plain unweighted mean** of that period's `subject_scores` -- source-tagged `"computed_unweighted_average"`, never presented as an official TBM or any school's real weighted average. This is a bare arithmetic mean, not a claim about how any school actually weights subjects.
- **Every trend delta is a bare arithmetic difference** (later score minus earlier score). There is no invented threshold for what counts as a "significant" or "meaningful" change -- direction is strictly `up` (delta > 0), `down` (delta < 0), or `flat` (delta == 0), with the exact numeric delta always shown alongside so the parent can judge magnitude themselves.

## What domain knowledge this validator encodes

- **Caller-declared chronological order, never inferred.** Each record has a required, unique integer `period_order` -- ordering is never guessed from list position or from the optional `date` field (which may be absent, or present only for some periods). This mirrors `legal-form-filler`'s "never guess a match" discipline applied to ordering instead of string matching.
- **0-10 numeric scale**, reused verbatim from `grade-book-builder`'s own documented convention (the well-known Vietnamese numeric grading scale format, not an official-citation claim).
- **Cross-period subject consistency is a warning, not an error.** A student may add or drop a subject across school years/terms (e.g. an elective starting in a later term) -- a subject present in some periods but missing in others is flagged informationally, and that subject's trend is computed only across the periods where it actually appears, rather than refusing the whole record.
- **A single-period record is valid, not an error** -- there's nothing structurally wrong with tracking one period so far; the result simply has no trend yet, flagged as a warning explaining why, consistent with this skill never inventing data to fill a gap.

## How to run

```bash
python scripts/track_progress.py <records.json> [--render summary.md] [--out result.json] [--force]
```

Start from `assets/progress_records_template.json`. Top-level: `student_name` (non-empty string), `records` (non-empty list). Each record:

| Field | Meaning |
| --- | --- |
| `period_label` | Non-empty string, e.g. "HK1 2025-2026". |
| `period_order` | Required unique integer -- the caller-declared chronological order. |
| `date` | Optional ISO `YYYY-MM-DD`, informational only, not used for ordering. |
| `subject_scores` | Non-empty object, subject name -> number in 0-10. |
| `reported_overall_average` | Optional number in 0-10 -- a real official average if the caller has one; omit/null to let this script compute a plainly-labeled unweighted mean instead. |

Exit 0 = structurally valid (trend computed if >=2 periods; warnings, if any, print above the VALID line). Exit 1 = at least one structural error (missing/wrong-type field, duplicate `period_order`, score outside 0-10, malformed date). Exit 2 = malformed input JSON, nonexistent file, or an existing `--render`/`--out` target without `--force`.

## What this skill does NOT do

- Does not grade or score any individual assessment -- that's `grading-and-feedback`. This only aggregates scores that already exist.
- Does not assert an official weighted average or classification (Gioi/Kha/Trung binh/Yeu) -- that domain judgment stays with `grade-book-builder` when a real school-declared weighting/banding scheme is available; this skill only ever computes an unweighted mean or passes through a caller-supplied reported average, verbatim.
- Does not invent a "significant change" threshold -- every delta is bare arithmetic, direction is strictly sign-based, no invented cutoff for how large a change must be to matter.
- Does not fetch or import data from any school system/API -- `records.json` is always a file the caller already has, prepared however they choose (manually, exported from another tool, etc.).
- Does not call any LLM/AI API -- pure deterministic arithmetic, no network of any kind.

## Verified

A valid 3-period record (Toan/Van/Anh across all 3 periods, `reported_overall_average` given for period 1 only, computed for periods 2-3) validated with zero errors; hand-verified Toan trend 8.0 -> 8.5 -> 8.2 produced deltas +0.5 (up) then -0.3 (down), overall_delta_first_to_last +0.2; rendered to both JSON and Markdown correctly. A record missing `student_name` correctly refused (exit 1). Two records sharing the same `period_order` (both `1`) correctly refused, naming the duplicate value. A `subject_scores` value of `12` (outside 0-10) correctly refused, naming the exact subject and value. Malformed JSON correctly refused (exit 2). A single-period record (only 1 entry in `records`) correctly validated (exit 0) with a warning explaining trend fields are empty pending a second period. A 2-period record where period 2 introduces a new subject ("Anh") absent from period 1 correctly validated (exit 0) with a warning naming the subject and which period lacks it, while Toan/Van trends still computed normally across both periods. A `reported_overall_average` of `15` (outside 0-10) correctly refused. A `date` of `"2026-02-30"` (not a real calendar date, February has no 30th) correctly refused by the ISO-date validator. `--render`/`--out` both correctly refused to overwrite an existing target without `--force`, and succeeded with `--force`.

## Known limitations (v0.1.0)

- `period_order` is a required manual integer -- if a caller mislabels the order (e.g. assigns period_order 1 to what was actually the later term), the trend direction will be backwards; this script has no way to detect that from `date` alone since `date` is optional and not cross-checked against `period_order` for consistency. A future version could add an optional warning if `date` values disagree with `period_order`'s sequence when both are present.
- No support for tracking more than one child in a single file -- `student_name` is a single required string; a family with multiple children needs one file per child.
- `computed_unweighted_average` is a plain arithmetic mean with no subject-count normalization concern beyond that -- a period with only 2 subjects scored and a period with 8 subjects scored are both averaged the same way, which may not reflect a real school's actual weighting even loosely; this is a known simplification consistent with the no-invented-official-numbers caveat, not an oversight.
- No visualization/chart output -- only a Markdown table and JSON; a future version could add a sparkline-style rendering if real use shows the need.
