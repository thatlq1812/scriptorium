---
name: competency-rubric-builder
description: Validates a competency/product/activity assessment rubric (rubric đánh giá năng lực/sản phẩm/hoạt động) record — a criteria × performance-levels table (3 or 4 levels, e.g. "Tốt / Đạt / Cần cố gắng") — checking every criterion has a non-empty observable-behavior description for every level, that criterion weights sum exactly to the declared total scale, and flagging (as a warning) any criterion whose level descriptions were copy-pasted identically across levels; then renders a clean Markdown rubric table. Use when drafting or checking a rubric before grading with it. Do NOT use this to judge whether the described behaviors are pedagogically appropriate for the subject/grade — it validates structure, arithmetic, and literal duplication only, never teaching quality.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-26). See "Verified" section below for real test-case detail.
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in EduStation's competency_rubric skill (D:/elix/edustation/skills/competency_rubric/SKILL.md, a real previously-deployed skill for K12 teachers) for the domain knowledge: a rubric is a tiêu chí (criteria, rows) × mức độ (performance levels, columns, high-to-low, 3 or 4 levels) table where every cell needs an observable-behavior description (explicitly not vague text like 'làm tốt'/'chưa tốt', called out as bad examples in the source), each criterion carries a trọng số (weight/max points) whose sum must exactly equal the declared thang_diem_tong, and level descriptions within one criterion should be distinct rather than repeated verbatim. Used loosely, not as a spec to follow literally — EduStation's own orchestration machinery (persona/effort/token_budget tuning, use_skill research-capability dispatch, Jinja2 profile placeholders, workspace-scan-before-work, script_exec DOCX build) was NOT ported; this skill is a single deterministic validator+Markdown renderer instead, with no LLM/AI call of any kind. Per owner direction (2026-07-26), this tier deliberately continues to skip EduStation's bureaucratic-paperwork skills in favor of skills that serve actual teaching/pedagogy work."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["rubric"]
---

# competency-rubric-builder

Validates a competency/product/activity assessment rubric (rubric đánh giá năng lực, sản phẩm học tập, hoặc hoạt động) — a table of criteria (tiêu chí) × performance levels (mức độ) — then renders it to clean Markdown. Catches missing cells, arithmetic mistakes, and copy-pasted level text deterministically, before the rubric is used to grade real students.

## Why this skill, and why this scope

Grounded in EduStation's real previously-deployed `competency_rubric` skill, but used loosely — the source is real tacit knowledge about what makes a rubric structurally sound, not a spec to copy. EduStation's SKILL.md packed in a large amount of harness-specific orchestration (persona/effort/token-budget tuning, `use_skill` dispatch to a research capability, Jinja2 profile placeholders, workspace-scan-before-work conventions, a `script_exec` DOCX build step) that is infrastructure for their own agent runtime, not domain knowledge — none of that was ported. What was worth keeping is the actual structural/pedagogical domain knowledge: the criteria × levels table shape, the "every cell needs an observable-behavior description, never vague text" rule, the "weights must sum to the declared scale" invariant, and the "level descriptions should be distinct within a criterion" quality signal — now encoded as a deterministic validator with no AI/network call anywhere.

Per the owner's continuing direction, this tier does not include any of EduStation's bureaucratic-paperwork skills — this skill validates a rubric used for actual student assessment, not an administrative document.

## What a structurally sound rubric requires (the domain knowledge this validator encodes)

- **A criteria × levels table**: rows are evaluation criteria (`tieu_chi`), columns are performance levels (`muc`) ordered from highest to lowest quality — 3 levels by default (e.g. "Tốt / Đạt / Cần cố gắng") or 4 levels (e.g. "Tốt / Khá / Đạt / Chưa đạt"). No other count is valid.
- **Every cell filled with an observable description**: for every `(tieu_chi, muc)` pair, `mo_ta` must have a non-empty description string. A missing cell is a hard error, named by exact criterion and level — never silently left blank.
- **Weights sum exactly to the declared scale**: each criterion's `trong_so` (weight/max points) must sum, across all criteria, to exactly `thang_diem_tong` (e.g. 10, or 100 for a percentage scale). Off by even a fraction is refused, with the actual sum and the exact shortfall/excess shown.
- **Distinct descriptions within a criterion**: a real, cheaply-detectable proxy for a lazy/copy-pasted rubric — if two levels of the *same* criterion carry identical description text, that's flagged as a warning (not a hard error, since text-identity is a mechanical check, not proof the content is actually vague).

## Run

```bash
python scripts/validate_rubric.py <rubric.json> [--render rubric.md] [--force]
```

Start from `assets/rubric_template.json` (a valid 3-level, 3-criteria example — Năng lực thuyết trình, weights 4+3+3=10 — read it for the exact JSON shape: `doi_tuong_danh_gia`, optional `khoi_lop`, `muc`, `thang_diem_tong`, `tieu_chi[].{ten, trong_so, mo_ta}`). Exit 0 = structurally valid (warnings may still print — read them, they flag copy-pasted level text), exit 1 = errors block (printed with field-level detail: exact criterion/level for missing cells, exact numbers for weight mismatches), exit 2 = malformed input, or `--render` target already exists without `--force`. `--render` only writes output when there are zero errors.

## What this skill does NOT do

- Doesn't judge whether the described behaviors are pedagogically appropriate for the subject/grade, whether the criteria chosen are the right ones, or whether the level descriptions are actually well-calibrated — pure structural/arithmetic/duplication validation.
- Doesn't generate rubric content itself (no LLM/AI call) — the teacher (or the agent working with the teacher) fills the JSON; this only checks it.
- Doesn't produce a `.docx` in the official A4/Times New Roman format — delegate that formatting step to `office-doc-creator` once the Markdown passes validation.
- Doesn't check that criteria/levels named in the rubric match any specific official framework (e.g. CT GDPT 2018 competency descriptors) — content-level correctness is out of scope, same as the structural-only stance in `lesson-plan-builder`.

## Verified

A valid 3-level/3-criteria rubric (weights 4+3+3=10) validated with zero errors and rendered to a clean Markdown table; a valid 4-level/3-criteria rubric (weights 25+25+50=100) also passed; a weight-sum mismatch (7 vs declared 10) was correctly refused showing the exact shortfall; a missing mo_ta cell was correctly refused naming the exact criterion and level; a criterion with identical description text copy-pasted across two levels correctly warned (not errored, exit 0); a 2-level muc, duplicate criterion names, a non-numeric trong_so, missing top-level fields, an empty tieu_chi list, and malformed/non-object JSON were all correctly refused; --render correctly declined to overwrite an existing file without --force and succeeded with it.

## Known limitations (v0.1.0)

- The duplication check is exact-text matching after whitespace trimming — a teacher who pads a copy-pasted description with a trivial word change ("làm tốt" vs "làm khá tốt") gets no warning even though the content is still effectively vague. Read a clean run as "no literal copy-paste found," not "descriptions are semantically distinct."
- No check that level descriptions are monotonically increasing in actual quality (e.g. that "Đạt" genuinely describes weaker performance than "Tốt") — that requires judging content, which this skill deliberately does not do.
- `khoi_lop` is accepted and rendered if present but never validated against any grade-level vocabulary or framework, unlike `lesson-plan-builder`'s CT GDPT 2018 checks — a rubric's criteria vocabulary is far more domain/activity-specific than a lesson plan's fixed competency set, so no fixed reference list was built for v0.1.0.
