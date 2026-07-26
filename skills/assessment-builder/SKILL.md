---
name: assessment-builder
description: Balances a Vietnamese K-12 exam matrix (ma trận đề) — topics × 4 cognitive levels (Nhận biết/Thông hiểu/Vận dụng/Vận dụng cao) — into an exact question-count + point allocation using a largest-remainder deterministic method, then validates that an actual exam (MCQ + essay) structurally and numerically matches that matrix. Use when a teacher needs to balance question/point counts for a test, quiz, question bank, exam set, sample/reference exam, or review outline, or to check a drafted exam against its intended matrix before printing. Do NOT use this to generate question CONTENT (no LLM call, ever — a human or the calling agent supplies the actual question text/answers) or to judge subject-matter correctness/difficulty — this validates matrix balance and structural conformance only.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-26) — build_exam_matrix.py verified to sum exactly to the requested total_questions/total_points across 8 combinations (few questions, one question, more topics than questions, uneven/non-100 ratios, weighted topics, 40-question/7-topic case, odd point totals); malformed input, missing topics, negative counts, duplicate topic names, and an unknown --profile were all correctly refused (exit 1) with a specific reason; refused to overwrite an existing output without --force (exit 2). validate_exam.py: a matching valid exam (10 MCQ + 10 essay against a 20-question/2-topic plan) passed with zero errors; 8 deliberately-broken exams (wrong MCQ choice count, duplicate choices, invalid answer label, missing question dropping a level count, an out-of-plan topic, an invalid level, a grading-guide sum mismatch, an off-total point sum) were each caught with the exact field/count/reason named; malformed JSON and an exam.json that is a JSON array both correctly refused (exit 1/2).
metadata:
  domain: education
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "Consolidates 6 EduStation skill folders that were all variations of the same 'generate an exam matrix + exam + answer key balanced by cognitive level' capability, differing only in output shape (D:/elix/edustation/skills/exam_builder, review_exam, sample_exam, question_bank, review_outline, tn_thpt_review — all SKILL.md read directly, plus exam_builder/scripts/build_dethi.py and its knowledge/ma_tran_de.md + knowledge/de_dap_an_format.md for the actual balancing-algorithm reference). Per owner direction (2026-07-26), consolidated into fewer, more practical skills rather than kept as 6 near-duplicate folders. Domain knowledge kept: the 4-cognitive-level framework (Nhận biết/Thông hiểu/Vận dụng/Vận dụng cao) and its default 40/30/20/10 ratio (explicitly a generic convention per EduStation's own knowledge/CURATION.md, not an official per-subject regulation), the largest-remainder (Hamilton apportionment) balancing method so counts/points always sum exactly, the MCQ invariant (exactly 4 distinct choices, exactly one valid answer), and the tn_thpt_review skill's QD 4068/QD-BGDDT THPT-graduation-exam profile concept (folded in here as a named --profile preset, not a separate skill, per the owner's explicit instruction). Domain knowledge deliberately DISCARDED: EduStation's harness-specific orchestration machinery in every one of the 6 SKILL.md files (persona/effort/token_budget tuning, use_skill/task_create/script_exec tool-call conventions, Jinja2 {{ user.* }}/{{ institution.* }} profile placeholders, workspace-scan-before-work digest conventions, planning-gate dialogue scripts) — none of that is domain knowledge, all of it is infrastructure for EduStation's own agent runtime. Also discarded: question_bank's per-question stable-code convention (<MON><khoi>-<chu de>.<muc>.<so thu tu>) and coverage-only (no total-point-balance) framing, tn_thpt_review's 3-answer-format (TN co dien + Dung/Sai + Tra loi ngan) QD 4068 structure and its per-subject ti_le_dang ratios — both are real domain knowledge but out of scope for a v0.1.0 that only covers the classic 4-level/MCQ+essay case; noted as a known limitation below for a possible v0.2+."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["exam", "exam-matrix", "question-bank"]
---

# assessment-builder

Balances a Vietnamese K-12 exam matrix (ma trận đề) by cognitive level, then validates that a drafted exam actually matches that matrix. Two deterministic, stdlib-only tools — no AI/LLM call anywhere in this skill.

## Why this skill, and why this scope

EduStation had 6 separate skill folders that were all the same core capability wearing a different output shape: `exam_builder` (one exam), `review_exam` (a set of exams), `sample_exam` (a reference/sample exam bound to an official exam's structure), `question_bank` (a reusable bank of tagged questions instead of one balanced exam), `review_outline` (a lighter review document, not fully matrix-balanced), and `tn_thpt_review` (a specific national-exam-format profile per QĐ 4068/QĐ-BGDĐT). Per the owner's explicit direction (2026-07-26), these were consolidated into one general-purpose matrix balancer + validator rather than kept as 6 near-duplicate folders. The QĐ 4068 case folds in as a `--profile` preset (a named ratio-set), not a separate skill — it is the same balancing algorithm with a different default ratio, not different domain logic.

EduStation's own SKILL.md files packed in a large amount of harness-specific orchestration (persona/effort/token-budget tuning, `use_skill`/`task_create`/`script_exec` dispatch conventions, Jinja2 `{{ user.* }}` profile placeholders, workspace-scan-before-work digest conventions, multi-page planning-gate dialogue scripts) that is infrastructure for their own agent runtime, not domain knowledge — none of that was ported. What WAS worth keeping is the real pedagogical/procedural domain knowledge: the 4-cognitive-level framework, the largest-remainder balancing method that keeps counts/points exact, and the MCQ structural invariants — now encoded as two clean, deterministic Python tools.

## What domain knowledge this skill encodes

- **Four cognitive levels, fixed vocabulary**: Nhận biết (recall) → Thông hiểu (comprehension) → Vận dụng (application) → Vận dụng cao (higher-order application/analysis/synthesis) — the standard Vietnamese K-12 ma trận đề framework.
- **Default ratio 40/30/20/10** (Nhận biết/Thông hiểu/Vận dụng/Vận dụng cao) — per EduStation's own `knowledge/ma_tran_de.md` and `knowledge/CURATION.md`, this is a **generic convention**, not an official per-subject/per-grade regulation. Always overridable via `level_ratio` in the input.
- **Largest-remainder (Hamilton apportionment) balancing**: question counts and point values are each apportioned across levels, then across topics within each level, so the parts always sum EXACTLY to the requested totals — never left to ad-hoc/LLM rounding, which drifts.
- **Zero-count cells get zero points**: a cognitive level (or topic × level cell) that receives 0 questions receives 0 points — its share of the ratio is redistributed (still by largest-remainder) across cells that actually have questions. (This was a real bug found during testing this session — see "Known limitations" below.)
- **MCQ invariant**: exactly 4 distinct, non-empty choices per multiple-choice question, and exactly one valid answer label.
- **Essay grading-guide invariant**: an essay question's `grading_guide` line items must sum to that question's own points (within a 0.01 tolerance) — a rubric that doesn't add up to the question's point value is structurally broken, independent of content quality.
- **QĐ 4068/QĐ-BGDĐT THPT-graduation-exam profile** (`--profile qd4068_thpt`): folded in as a named ratio-set preset — see "Known limitations" for exactly how modest this is.

## How to run

### 1. Build the balanced matrix

```bash
python scripts/build_exam_matrix.py <input.json> -o plan.json [--render matrix.md] [--profile qd4068_thpt] [--force]
```

Start from `assets/exam_matrix_input_template.json`:

```json
{
  "topics": [{"name": "Đại số", "weight": 1}, {"name": "Hình học", "weight": 1}],
  "total_questions": 20,
  "total_points": 10,
  "level_ratio": {"nhan_biet": 40, "thong_hieu": 30, "van_dung": 20, "van_dung_cao": 10}
}
```

- `topics` — a list of strings, or objects with `name` (required) + `weight` (optional, default 1 — a topic covering more content can be given a higher weight to earn more questions).
- `total_questions` / `total_points` — required.
- `level_ratio` — optional; percentages need not sum to exactly 100 (rescaled proportionally); missing entirely falls back to the profile default (40/30/20/10 unless `--profile` says otherwise).
- `--profile` — selects a named default ratio-set when the input doesn't override `level_ratio` (see "Known limitations" for what profiles actually exist and mean).

Exit 0 = plan written (stdout prints the count/point sums against the expected totals as a sanity echo); exit 1 = invalid input (reason printed to stderr); exit 2 = output path exists and `--force` wasn't given.

The output `plan.json` is the single source of truth: `level_counts`/`level_points` (per cognitive level) and `grid_counts`/`grid_points` (per topic × level cell). `--render` additionally writes a human-readable Markdown matrix table.

### 2. Fill in the actual exam content (human or calling agent — not this skill)

Using `plan.json`'s allocation as the target shape, write `exam.json` following `assets/exam_template.json`:

```json
{
  "mcq": [{"question": "...", "choices": ["...", "...", "...", "..."], "answer": "A", "topic": "Đại số", "level": "nhan_biet", "points": 0.25}],
  "essay": [{"question": "...", "topic": "Đại số", "level": "van_dung", "points": 1.0, "grading_guide": [{"criterion": "...", "points": 0.5}]}]
}
```

This skill never generates question text/answers itself — no LLM/AI call of any kind, per this project's no-AI-backend principle. A human teacher or the calling agent supplies real content; this skill only balances and checks it.

### 3. Validate the exam against the plan

```bash
python scripts/validate_exam.py plan.json exam.json
```

Checks, and refuses loudly (nonzero exit, naming exactly what's off) on any mismatch:

- total question count (MCQ + essay combined) matches `plan.total_questions`;
- question count per cognitive level (MCQ + essay combined) matches `plan.level_counts`;
- question count per (topic × level) cell matches `plan.grid_counts`;
- every MCQ has exactly 4 distinct, non-empty choices and exactly one valid answer label;
- every essay's `grading_guide` sums to that essay's own `points` (0.01 tolerance);
- total points (MCQ + essay combined) matches `plan.total_points` (0.01 tolerance).

Exit 0 = valid (conformance only — not a judgment on question quality/correctness); exit 1 = one or more mismatches, each printed with the specific field/count/expected-vs-actual; exit 2 = malformed/non-object JSON input.

### 4. DOCX rendering — not bundled here

This skill produces JSON (the plan) and validates JSON (the exam) — it does not render a `.docx` matrix table, exam paper, or answer key. Once `exam.json` passes `validate_exam.py`, hand the validated JSON/its Markdown rendering to `office-doc-creator` (`D:/elix/scriptorium/skills/office-doc-creator/`) for the actual document, matching the delegation pattern `literature-review` uses for its own optional PDF/DOCX step.

## What this skill does NOT do

- Doesn't generate question content, answers, or grading rubrics — no LLM/AI call of any kind. A human or the calling agent supplies real content; this skill only balances and validates structure/numbers.
- Doesn't judge subject-matter correctness, difficulty calibration, or pedagogical quality of a question — pure structural/numeric conformance to the matrix.
- Doesn't render `.docx` — delegate to `office-doc-creator` once `exam.json` passes validation.
- Doesn't implement the QĐ 4068 3-answer-format (TN cổ điển + Đúng/Sai + Trả lời ngắn) structure or per-subject official ratio tables — see "Known limitations".
- Doesn't implement question-bank-style stable question codes/coverage tracking (EduStation's `question_bank` skill) or a bộ-đề (exam-set)/multi-exam batch mode (EduStation's `review_exam`) — a single matrix + a single exam per run in v0.1.0.

## Known limitations (v0.1.0)

- **`--profile qd4068_thpt` is a name only, not a verified official ratio table.** It currently maps to the exact same 40/30/20/10 default as `--profile default`, mirroring what EduStation's own `tn_thpt_review` skill used as ITS default (itself sourced from one 18/10/2024 sample-exam Bloom ratio for the natural-science subject group, per that skill's `knowledge/CURATION.md` — never an official per-subject regulation lookup). Do not present a `qd4068_thpt` plan as "the official QĐ 4068 structure" — it is a labeled convenience default, exactly as honest as the source it was elicited from.
- **No 3-answer-format support.** QĐ 4068 (THPT graduation exam from 2025) actually requires 3 answer formats per question (TN 4-phương-án + Đúng/Sai 4-ý + Trả lời ngắn), not classic MCQ + essay. This v0.1.0 only supports the classic MCQ (4 choices, 1 answer) + essay (points + grading guide) shape. Adding the 3-format structure is a reasonable v0.2+ addition if real use shows the need — flagged, not built, to keep this session's scope testable end-to-end.
- **No stable per-question code / coverage-tracking mode.** EduStation's `question_bank` skill tagged each question with a stable code (`<MÔN><khối>-<chủ đề>.<mức>.<số thứ tự>`) for cross-exam reuse and tracked coverage independent of point-balance. This skill only produces one point-balanced exam per plan; reusable tagged banks are out of scope for v0.1.0.
- **No multi-exam batch mode.** EduStation's `review_exam` balanced N exams in one call (a bộ đề). This skill balances one matrix at a time — call `build_exam_matrix.py` once per exam in a set; there is no batch/index.json convenience layer.
- **Topic weighting is a plain proportional weight, not a curriculum-hours or difficulty-adjusted weight.** A `weight: 3` topic gets roughly 3x the questions of a `weight: 1` topic — it does not know anything about actual instructional-hour allocation per topic; the caller supplies weights that reflect that if desired.
- **`grading_guide` sum-check is a structural add, not explicitly requested by the original design brief.** It was added because a rubric whose line items don't sum to the question's own points is a genuinely broken artifact (independent of content quality) and is cheap to catch deterministically; it can be loosened if a real workflow needs partial/discretionary-points rubrics that don't sum exactly.
- **The zero-count-cell-gets-zero-points fix was found by testing, not designed in from the start.** A very small `total_questions` relative to the number of levels (e.g. 2 questions across 4 levels) originally left points allocated to a cognitive level that ended up with 0 questions — an impossible-to-realize plan. Fixed by zeroing that level/cell's weight before apportioning points, so points only ever land on cells that actually have questions. Covered by the `one_question` test case in this session's manual testing (see `compatibility` field).
