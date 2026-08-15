---
name: grade-book-builder
description: Aggregates already-scored assessment results into a class-wide term gradebook (so tong hop diem) — deterministically computes each student's weighted term average (TBM) across multiple assessment categories (e.g. mieng/giua_ky/cuoi_ky), classifies each student against user-declared bands (e.g. Gioi/Kha/Trung binh/Yeu), and produces class statistics — then renders a Markdown summary table. Use when a teacher/giao vu already has per-assessment scores for a class and needs the term-level rollup. Do NOT use this to grade or score an individual assessment (that's `grading-and-feedback`), and do NOT use it as a source of official TT22/2021 weight percentages or classification thresholds — those are required inputs the caller must declare, this skill does not assert or invent them.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-26). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in prior system's grade_book skill (prior deployed system skills/grade_book/SKILL.md, a real previously-deployed skill for K12 school staff) for the domain shape only: a class gradebook has student rows, weighted assessment-category columns, a computed term-average (TBM) column, and a computed classification (xep loai) column — and the general Vietnamese convention that THCS/THPT commonly weight diem thuong xuyen/giua ky/cuoi ky differently (that source's own text: 'DDGtx he so 1 / DDGgk he so 2 / DDGck he so 3 theo TT22, hoac theo quy uoc truong'), explicitly flagged in that source itself as a reference default the caller must confirm, not a mandate ('neu ro trong plan day la thang tham khao, khong phai menh lenh'). No exact official TT22/2021 weight percentages or classification score thresholds were found stated as verified fact in the source material available, so per STRATEGY_SPEC.md Section 7 principle 5 (never fabricate legal/regulatory citations), this skill does NOT hardcode any such numbers — category_weights and classification_bands are both required caller-declared inputs with no built-in default values, and assets/gradebook_template.json's 1/2/3 weights and 4-band labels are illustrative placeholders only, not asserted official figures. prior system's own orchestration machinery for this skill (xlsx_read/xlsx_write/script_exec tool-call sequencing, workspace-scan-before-work, planning-gate HITL dialogue, live-Excel-formula construction via openpyxl SUMPRODUCT/IF) was NOT ported; this is a single deterministic JSON-in/JSON-and-Markdown-out calculator instead. Per thatlq1812 direction (2026-07-26), this tier deliberately excludes prior system's bureaucratic-paperwork skills; grade-book-builder itself stays scoped to teaching-adjacent recordkeeping, not administrative correspondence."
  version: 0.1.0
  grounding: required
  object_type: ["gradebook"]
---

# grade-book-builder

Aggregates already-scored assessment results into a class-wide term gradebook: each student's weighted term average (TBM — trung binh mon) across multiple declared assessment categories, a classification against declared bands (xep loai), and class-wide statistics. Renders a clean Markdown summary table alongside the JSON result.

## Why this skill, and why this scope

Third skill for the Teacher audience tier (`docs/specs/STRATEGY_SPEC.md` §5.1), grounded in prior system's real previously-deployed `grade_book` skill — used loosely for domain shape (student rows × weighted category columns × computed TBM/xep-loai columns), not copied as a spec. prior system's version was a live-Excel-formula generator (openpyxl `SUMPRODUCT`/`IF`, workspace file scanning, a planning-gate dialogue with the school staff user) built for their own agent runtime — none of that orchestration machinery was ported. What was worth keeping is the actual arithmetic shape: a class gradebook is a weighted average per student (average within a category first, then weight across categories), plus a classification lookup, plus class statistics. This skill re-implements that shape as a single deterministic calculator with no AI/network dependency of any kind.

Per thatlq1812's direction (2026-07-26), the Teacher tier deliberately does not include prior system's bureaucratic-paperwork skills — this skill stays scoped to a teaching-adjacent recordkeeping artifact (the term gradebook), not administrative correspondence.

## The one hard caveat: no invented official numbers

prior system's own SKILL.md for `grade_book` explicitly flags its TT22-shaped 1/2/3 weight example as a **reference default the school-staff user must confirm, not a mandate** ("nêu rõ trong plan đây là thang tham khảo, không phải mệnh lệnh"). No exact official TT22/2021 weight percentages or classification score thresholds were found stated as verified fact anywhere in the available source material. Per `docs/specs/STRATEGY_SPEC.md` §7 principle 5 (never fabricate legal/regulatory citations), this skill **does not hardcode any official weight or banding numbers**:

- `category_weights` has no built-in default — every category and its weight must be declared by the caller.
- `classification_bands` has no built-in default — every label and its threshold must be declared by the caller.
- `assets/gradebook_template.json`'s example values (1/2/3 weights, Gioi/Kha/Trung binh/Yeu at 8.0/6.5/5.0/0.0) are illustrative placeholders only, not an asserted official scale. Replace them with your school's actual declared weights/bands before use.

## What domain knowledge this skill encodes

- **Two-stage weighted average**: within a category, average all scores in that category first (e.g. multiple `mieng` scores → one category average); then take the weighted sum of category averages, divided by the actual total of the declared weights (not assumed to be 1.0 — `weight_total` is validated against the true sum of `category_weights`, whatever scale the caller uses, e.g. summing to 6 like 1+2+3, or to 1.0 like 0.1+0.3+0.6).
- **0-10 score scale**: individual scores are checked against the standard Vietnamese 0-10 numeric grading scale (not an official-citation claim — this is the well-known scale format, distinct from the weight/banding numbers this skill deliberately does not assert).
- **Descending-threshold classification**: `classification_bands` is a caller-ordered list of `{label, min_score}`; a student's TBM is matched to the first band (highest threshold first) whose `min_score` it meets or exceeds. The list must be strictly descending — this is validated, not assumed.
- **Referential integrity between weights and scores**: every category a student scores in must be declared in `category_weights`, and every category declared in `category_weights` must be used by at least one student — both directions are checked, refusing loudly and naming the mismatched category rather than silently ignoring it.

## How to run

```bash
python scripts/build_gradebook.py <gradebook.json> [--render summary.md] [--out result.json] [--force]
```

Start from `assets/gradebook_template.json`. Exit 0 = computed successfully (prints the class TBM average to stdout; with no `--render`/`--out`, the full JSON result prints to stdout). Exit 1 = refused with field-level error detail (weight-sum mismatch, unknown/missing/unused category, out-of-range score, misordered bands, duplicate student id). Exit 2 = malformed input JSON, nonexistent file, or an existing `--render`/`--out` target without `--force`.

## What this skill does NOT do

- Does not grade or score any individual assessment (essay, quiz, assignment) — that is `grading-and-feedback`, a separate skill. This skill only aggregates scores that already exist.
- Does not assert official TT22/2021 weight percentages or classification-band thresholds as verified fact — see "The one hard caveat" above. `category_weights` and `classification_bands` are always required, caller-declared inputs.
- Does not produce a `.xlsx`/`.docx` gradebook file with live spreadsheet formulas — delegate rendering the final gradebook to a document format to `office-doc-creator` once the JSON/Markdown result is correct. (Unlike prior system's original, this skill computes the numbers itself in Python; it does not write Excel formula strings.)
- Does not call any LLM/AI API — pure deterministic arithmetic, no network of any kind.

## Verified

A valid 3-student/3-category class computed correctly (hand-verified: student A weighted sum 8.5*1+7*2+8*3=46.5 / weight_total 6 = 7.75 -> rounds to 7.8, classified Kha; class average across 3 students 7.7), rendered to Markdown and JSON correctly; a category_weights sum mismatch (declared weight_total 10 vs actual sum 6) correctly refused showing both numbers; a student using an undeclared category correctly refused naming the unknown category; a student missing a declared category correctly refused; a category declared but never used by any student correctly refused; a score outside the 0-10 scale correctly refused; classification_bands out of descending order correctly refused; a duplicate student id correctly refused; malformed JSON and a nonexistent input file both correctly exited 2; render/--out both correctly refused to overwrite without --force and succeeded with --force.

## Known limitations (v0.1.0)

- Every declared category currently requires at least one score from every student (no partial/missing-category handling for, e.g., a student who was absent for one assessment type all term) — a student missing any declared category is refused rather than averaged over the remaining categories. This keeps the weighted-average arithmetic unambiguous, but a future version could add an explicit `"absent"` marker per category if real use shows the need.
- Score validation only checks the 0-10 numeric range; it does not distinguish between different assessment weight conventions some schools use (e.g. 0-100 scale converted, or letter grades) — inputs must already be on the 0-10 scale.
- `classification_bands` matching is a single global scale per gradebook file — no support yet for level-adaptive bands (e.g. a different scale for Tieu hoc vs THCS/THPT) within one gradebook run; run the script once per level/scale if a school needs different bands per level.
- No cross-check against a roster or attendance system — `students` is exactly the list given in the input file; a student not listed simply isn't in the output.
