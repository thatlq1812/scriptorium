---
name: lesson-plan-builder
description: Validates a K-12 Vietnamese lesson plan (KHBD) record against the mandatory structure of Phu luc IV, Cong van 5512/BGDDT-GDTrH — exactly 4 activities in fixed order, each with all 4 required sub-parts, a fixed competency/quality-trait vocabulary (CT GDPT 2018), and level-appropriate assessment language (TT27 for tieu hoc: no scores; TT22 for THCS/THPT: scores allowed) — then renders a clean Markdown KHBD. Use when drafting or checking a lesson plan for structural completeness before class. Do NOT use this to judge whether the pedagogy itself is good — it validates structure and fixed vocabulary only, never teaching quality.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, re, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-26). See "Verified" section below for real test-case detail.
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in prior system's lesson_plan skill (prior deployed system skills/lesson_plan/SKILL.md, a real previously-deployed skill for K12 teachers) for the CV5512 domain knowledge: the mandatory 5-section structure, the fixed CT GDPT 2018 vocabulary (5 pham chat, 3 nang luc chung, 7 nang luc dac thu candidates), the level-adaptive assessment rule (TT27 tieu hoc = remarks only, TT22 THCS/THPT = scores allowed), and the 'pham chat/nang luc declared in muc tieu must be named in at least one activity' quality check. Deliberately used loosely, not as a spec to follow literally (owner's explicit caveat, 2026-07-26) -- prior system's own orchestration machinery (persona/effort/token_budget/multi-turn sub-agent dispatch, Jinja2 profile placeholders, workspace-scan-before-work) was NOT ported; this skill is a single deterministic validator+renderer instead. Per owner direction (2026-07-26), this tier deliberately skips prior system's bureaucratic-paperwork skills (annual_report/correspondence_log/directive_letter/meeting_minutes/school_decision/etc. -- Nghi dinh 30/2020 administrative templates) in favor of skills that serve the actual teaching/pedagogy work."
  version: 0.1.0
  grounding: required
  object_type: ["lesson-plan"]
---

# lesson-plan-builder

Validates a K-12 lesson plan (Kế hoạch bài dạy — KHBD) against the mandatory structure of Phụ lục IV, Công văn 5512/BGDĐT-GDTrH, then renders it to clean Markdown. Catches structural/vocabulary mistakes deterministically, before they reach a classroom.

## Why this skill, and why this scope

First skill for the **Teacher** audience tier (`docs/specs/STRATEGY_SPEC.md` §5.1), grounded in prior system's real previously-deployed `lesson_plan` skill — but used loosely per the owner's explicit instruction, not copied as a spec ("dựa thôi chứ không phải tham khảo hẳn, vì tôi biết nó vẫn yếu"). prior system's SKILL.md packed in a large amount of harness-specific orchestration (persona/effort/token-budget tuning, batched sub-agent dispatch to avoid a specific timeout bug, Jinja2 profile placeholders, workspace-scan conventions) that is infrastructure for their own agent runtime, not domain knowledge — none of that was ported. What WAS worth keeping is the actual pedagogical/legal domain knowledge: the CV 5512 structure, the fixed CT GDPT 2018 competency vocabulary, and the level-adaptive assessment rule — real tacit knowledge elicited from a real deployed system, now encoded as a deterministic validator.

Per the owner's direction (2026-07-26), the Teacher tier deliberately does **not** include prior system's bureaucratic-paperwork skills (annual reports, correspondence logs, directive letters, meeting minutes, school decisions — all Nghị định 30/2020 administrative templates). Those serve school-administration process, not the actual teaching work this tier is meant to serve.

## What CV 5512 requires (the domain knowledge this validator encodes)

- **Exactly 4 activities, fixed order, fixed names**: Khởi động → Hình thành kiến thức mới → Luyện tập → Vận dụng. Never reordered, renamed, merged, or split.
- **Each activity needs 4 sub-parts**: a) Mục tiêu, b) Nội dung, c) Sản phẩm, d) Tổ chức thực hiện — and (d) itself needs 4 steps: Chuyển giao nhiệm vụ → Thực hiện nhiệm vụ → Báo cáo, thảo luận → Kết luận, nhận định.
- **Mục tiêu uses a fixed 3-part structure**: kiến thức (free text) + năng lực (3 fixed năng lực chung + subject-specific năng lực đặc thù) + phẩm chất (fixed to exactly 5: Yêu nước, Nhân ái, Chăm chỉ, Trung thực, Trách nhiệm — from CT GDPT 2018, Thông tư 32/2018).
- **Level-adaptive assessment**: `khoi_lop` 1-5 (Tiểu học) → TT 27/2020 → remarks only, no scoring language allowed in `danh_gia`. `khoi_lop` 6-12 (THCS/THPT) → TT 22/2021 → scoring allowed.
- **Quality cross-check (not just form-filling)**: every phẩm chất/năng lực declared in `muc_tieu` should be named, by exact text, in at least one activity's own mục tiêu — otherwise it's a declared-but-undeveloped competency (a warning, not a hard error, since text matching is literal).

## Run

```bash
python scripts/validate_lesson_plan.py <plan.json> [--render plan.md]
```

Start from `assets/lesson_plan_template.json`. Exit 0 = structurally valid (warnings may still print — read them, they're pedagogical quality signals), exit 1 = errors block (printed with field-level detail), exit 2 = malformed input. `--render` only writes output when there are zero errors.

## What this skill does NOT do

- Doesn't judge pedagogy quality, content accuracy, or whether the activities are actually good teaching — pure structural/vocabulary/cross-reference validation.
- Doesn't generate the lesson content itself (no LLM/AI call) — the teacher (or the agent working with the teacher) fills the JSON; this only checks it.
- Doesn't produce a `.docx` in the official Times New Roman 14 / 2.5-2.0-2.0-2.0cm margin format — delegate that formatting step to `office-doc-creator` once the Markdown passes validation.
- Doesn't cover any of the administrative-paperwork document types (reports, decisions, correspondence logs, meeting minutes) — deliberately out of scope for this tier, see "Why this skill" above.

## Verified

A real 4-activity THCS lesson plan (Toán, số nguyên tố) validated with zero errors/warnings and rendered correctly to Markdown; a Tiểu học (grade 3) plan with scoring language correctly errored citing TT27; a deliberately broken plan (wrong activity order, invalid phẩm chất/năng lực vocabulary, missing to_chuc_thuc_hien steps) correctly caught 7 errors + 3 cross-reference warnings; missing-fields and malformed-JSON cases correctly refused; a time-allocation mismatch (45 vs 90 declared minutes) correctly warned at the 5% tolerance threshold.

## Known limitations (v0.1.0)

- The "competency named in an activity" cross-check is literal substring matching — a teacher who paraphrases a competency name instead of using it verbatim will get a spurious warning. Read warnings as prompts to double-check, not infallible findings.
- `nang_luc_dac_thu` is only soft-validated (warns if outside the 7-item CT GDPT 2018 reference list) since subject-specific competency names legitimately vary more than the fixed pham_chat/nang_luc_chung sets.
- No support yet for `theme_lesson_plan`-style multi-lesson themed units or `cross_subject_plan`-style interdisciplinary/STEM lesson plans (both real prior system variants) — v0.1.0 covers the single-lesson case only; a future version could add these as additional structure profiles if real use shows the need.
