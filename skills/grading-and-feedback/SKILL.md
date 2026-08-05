---
name: grading-and-feedback
description: Deterministically aggregates/validates ONE exam's scores (MCQ answer-key matching + human-scored essay/rubric criteria capped at each criterion's declared max) into per-student totals and class statistics, lints qualitative student remarks for level-appropriate assessment language (TT27 tiểu học forbids scoring language, TT22 THCS/THPT allows it — reusing lesson-plan-builder's proven SCORE_LANGUAGE_RE pattern), and provides a local-only HSnn roster-anonymization round-trip. Use when grading one assessment (MCQ/essay/mixed) or drafting student remarks for one reporting period. Do NOT use this to compute a term average (TBM) or overall grade classification (xếp loại) across multiple assessments — that is grade-book-builder's job. Do NOT use this to produce the final .docx/.xlsx report — delegate that to office-doc-creator. This never grades essay content itself and never calls an LLM/AI API — it only aggregates/validates scores a human (or an upstream process) already assigned.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, re, argparse, collections) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-26). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in three real previously-deployed prior system skills (prior deployed system skills/): (1) grading/SKILL.md (fullest spec) for the core domain knowledge kept here — MCQ scoring must be 100% deterministic answer-key matching, never LLM-estimated (mirrored from its own scripts/grade_mcq.py, reimplemented cleanly rather than copied: exact-match after case/whitespace normalization, a missing answer always counts wrong never correct, an answer to a question not in the key is ignored); essay/rubric scoring is per-criterion, capped at each criterion's declared max, total = sum of criteria, never exceeding the rubric's max (this skill hardens that rule into a hard refusal rather than the source's model-driven scoring, since this skill's essay scores arrive already-assigned by a human/upstream process and are only aggregated/validated, per this project's no-AI-backend principle); and the anonymization safety pattern -- student identities anonymized to HS01/HS02 codes for any content that would touch an LLM, with a LOCAL-ONLY mapping table re-attaching real names only at the final step, justified by Vietnam's 'Quy chế AI Điều 6' student-PII data-sensitivity rule. (2) primary_remarks/SKILL.md for TT27/2020 tiểu học remark rules: numeric/scoring language is forbidden in a regular-lesson remark. (3) report_card_remarks/SKILL.md for TT22/2021 THCS/THPT remark rules: scoring language is allowed, unlike TT27. The level-appropriate language check itself reuses (not re-derives) the SCORE_LANGUAGE_RE pattern and TH-vs-THCS/THPT branching logic already proven correct in this repo's own skills/lesson-plan-builder/scripts/validate_lesson_plan.py, per the owner's explicit direction to reuse it rather than reinvent it. None of prior system's harness-specific orchestration machinery (persona/effort/token_budget tuning, batched sub-agent dispatch, Jinja2 profile placeholders, workspace-scan-before-work conventions, use_skill/script_exec/llm_call tool calls) was ported -- this skill is three deterministic stdlib scripts instead, matching this project's 'no AI backend integration' principle: it never grades essay content or composes remark text itself, it only validates/aggregates numbers and lints language a human (or the consuming agent's own backend) already produced."
  version: 0.1.0
  grounding: required
  object_type: ["exam", "gradebook", "remark"]
---

# grading-and-feedback

Deterministically aggregates and validates scores for ONE exam (MCQ + human-scored essay/rubric), lints student remarks for level-appropriate assessment language, and provides a local-only roster-anonymization round-trip for any workflow step that would otherwise expose student PII.

## Why this skill, and why this scope

Consolidates three real previously-deployed prior system skills that all sit around the same scoring/feedback moment — grading (MCQ + essay), primary_remarks (Tiểu học qualitative remarks under TT27), and report_card_remarks (THCS/THPT qualitative remarks under TT22) — into one skill for the Teacher tier, per the owner's explicit direction to consolidate prior system's ~63 over-fragmented skill folders into fewer, more practical ones. prior system's own SKILL.md files packed in a large amount of harness-specific orchestration (persona/effort/token_budget tuning, batched sub-agent dispatch, Jinja2 profile placeholders, workspace-scan-before-work, `use_skill`/`script_exec`/`llm_call` tool calls) that is infrastructure for their own agent runtime, not domain knowledge — none of that was ported.

What WAS worth keeping: the deterministic-arithmetic discipline (never let an LLM add up scores or estimate a mark), the per-criterion rubric-capping rule, the HSnn anonymization pattern for student PII, and the level-adaptive remark language rule (same TT27-vs-TT22 shape lesson-plan-builder already encodes for `danh_gia` in a lesson plan). This skill re-derives none of the TT27/TT22 language check — it reuses the exact `SCORE_LANGUAGE_RE` pattern and TH-vs-THCS/THPT branching already proven correct in `skills/lesson-plan-builder/scripts/validate_lesson_plan.py`.

Per owner direction, this tier deliberately excludes prior system's bureaucratic-paperwork skills (Nghị định 30/2020 administrative templates) — this skill serves the actual scoring/feedback work, not administrative process.

## What domain knowledge this skill encodes

- **MCQ scoring is 100% deterministic answer-key matching, never LLM-estimated.** Case/whitespace-insensitive exact match. A missing or blank answer always counts wrong, never correct. An answer to a question not in the key is ignored.
- **Essay/rubric scoring is per-criterion, capped at that criterion's declared max.** Total essay score = sum of criteria. A criterion score exceeding its own `max_points` is refused outright — never silently clamped, never accepted. This script does not grade essay content itself; scores arrive already-assigned by a human or an upstream process and are only aggregated/validated.
- **Combined total = MCQ score + essay total** (whichever sections the answer key declares). Class statistics (mean/max/min/count) are computed over combined totals.
- **Level-adaptive remark language**: `grade_level` 1-5 (Tiểu học) → TT27/2020 → no scoring language (`cho điểm`/`chấm điểm`/`điểm số`) and no bare numeric-grade pattern (e.g. `8/10`, `9 điểm`, `điểm: 7`) in a regular-lesson remark — hard error. `grade_level` 6-12 (THCS/THPT) → TT22/2021 → scoring language allowed, no restriction.
- **Student PII anonymization (Quy chế AI Điều 6)**: any workflow step that would touch an LLM/network call must work on `HSnn` codes only. Real names are mapped locally and re-attached only at the final, purely local step — never sent anywhere.

## How to run

### 1. Grade one exam

```bash
python scripts/grade_exam.py <answer_key.json> <student_responses.json> [--out results.json]
```

Start from `assets/answer_key_template.json` (declare `mcq`, `rubric`, or both) and `assets/student_responses_template.json`. Essay scores in the responses file must already be assigned (by a teacher or an upstream process) — this script aggregates and validates, it does not grade essay content. Exit 0 = graded cleanly (prints per-student results + class stats, writes `--out` if given); exit 1 = refused (a criterion score exceeds its max, a duplicate student/criterion, an unknown criterion name, a negative score — no output written); exit 2 = malformed input.

### 2. Lint a batch of remarks for level-appropriate language

```bash
python scripts/lint_remarks.py <remarks.json>
```

Input: `{ "grade_level": <1-12>, "remarks": [ { "student_id", "text" }, ... ] }`. `grade_level` 1-5 hard-errors on scoring language/numeric-grade patterns (TT27); 6-12 allows them (TT22). Also hard-errors on blank/placeholder remarks. Soft-warns (does not block) when ≥3 students share verbatim identical remark text — a templated-content quality smell. Exit 0 = clean (warnings may still print); exit 1 = errors; exit 2 = malformed input.

### 3. Anonymize/reattach a roster (local-only)

```bash
python scripts/anonymize_roster.py anonymize <roster.json> --out roster_map.json
python scripts/anonymize_roster.py reattach <results.json> roster_map.json --out results_named.json
```

`anonymize` assigns stable `HS01`, `HS02`, ... codes in class-list order (zero-padded to fit the roster size) and writes a local mapping file — **this file is SENSITIVE and LOCAL-ONLY; never send its contents to any LLM/network call.** Use the codes for every step that would otherwise touch student PII (e.g. essay-scoring prompts, remark composition). `reattach` walks a results JSON document recursively and replaces every string matching a mapped code (in both values and dict keys) with the real name, using only the local mapping file — never over a network. Exit 0 = success; exit 1 = refused (output exists without `--force`, or no code from the mapping was found in the results); exit 2 = malformed input.

## What this skill does NOT do

- Does not compute a term average (TBM) or an overall grade classification (xếp loại) across multiple assessments — that's `grade-book-builder`'s job (a separate skill). This skill only grades ONE assessment.
- Does not produce the final `.docx`/`.xlsx` report — delegate that to `office-doc-creator` once scores/remarks pass validation.
- Does not grade essay content, generate rubric scores, or compose remark text — no LLM/AI call anywhere in this skill. Essay scores must already be assigned by a human or an upstream process before `grade_exam.py` sees them; remark text must already be written before `lint_remarks.py` checks it.
- Does not verify that a `roster.json`/`roster_map.json` mapping is actually correct, or that a name was really re-attached to the right student — it verifies structure and performs the substitution, not the ground truth of the roster.
- Does not judge remark accuracy, pedagogical quality, or whether the remark's content is actually true — `lint_remarks.py` checks assessment-LANGUAGE rules only.

## Verified

grade_exam.py graded a 3-student class (MCQ + rubric) correctly including one student with a missing/partial MCQ answer and one with no essay scores at all, refused an essay score exceeding its criterion's max_points with no output written, and correctly refused malformed JSON, an answer key with neither mcq nor rubric, a negative score, an unknown criterion name, a duplicate criterion, and a duplicate student_id. lint_remarks.py correctly passed a clean Tiểu học batch, errored on Tiểu học remarks containing scoring language and numeric-grade patterns (TT27), passed the identical text on a THCS batch (TT22 allows scores), warned (not errored) on 3 students sharing verbatim identical remark text, and errored on blank/placeholder remarks. anonymize_roster.py round-tripped anonymize→grade-by-code→reattach correctly on a 3-student and a 105-student roster (zero-padding verified: HS001/HS100/HS105), and correctly refused an overwrite without --force, an empty roster, a roster entry missing full_name, and a reattach with no matching codes.

## Known limitations (v0.1.0)

- `lint_remarks.py`'s numeric-grade pattern is a hand-curated regex (`8/10`, `9 điểm`, `điểm: 7` shapes). A differently-worded score reference (e.g. spelled-out numbers, "đạt loại giỏi") will not be caught — a safety net, not a guarantee.
- The duplicate-remark warning is exact-text matching after whitespace normalization; a paraphrased near-duplicate will not be flagged. Threshold is fixed at ≥3 identical remarks — not configurable in v0.1.0.
- `anonymize_roster.py`'s `reattach` mode does a blind string-equality substitution recursively through the JSON document. If a legitimate data value happens to equal an assigned code exactly (e.g. a question ID literally named "HS01"), it will also be replaced — a low-probability collision given the `HSnn` code shape, but not structurally prevented.
- `grade_exam.py` trusts that essay scores in the input were legitimately assigned by a human/process; it has no way to detect a fabricated or careless score that still happens to fall within a criterion's valid range.
- None of these three scripts talk to each other automatically — the consuming agent/teacher is responsible for anonymizing before any LLM-touching step, running `grade_exam.py`/`lint_remarks.py` on the anonymized data, and reattaching names only at the final local step.
