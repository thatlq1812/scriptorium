---
name: lesson-plan-builder
description: 'Validates a K-12 Vietnamese lesson plan (KHBD) record against the mandatory structure of Phu luc IV, Cong van 5512/BGDDT-GDTrH — exactly 4 activities in fixed order, each with all 4 required sub-parts, a fixed competency/quality-trait vocabulary (CT GDPT 2018), and level-appropriate assessment language (TT27 for tieu hoc: no scores; TT22 for THCS/THPT: scores allowed) — then renders a clean Markdown KHBD. Use when drafting or checking a lesson plan for structural completeness before class. Do NOT use this to judge whether the pedagogy itself is good — it validates structure and fixed vocabulary only, never teaching quality.'
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, re, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-26; re-verified at v0.2.0, 2026-08-13). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in prior system's lesson_plan skill (prior deployed system skills/lesson_plan/SKILL.md, a real previously-deployed skill for K12 teachers) for the CV5512 domain knowledge: the mandatory 5-section structure, the fixed CT GDPT 2018 vocabulary (5 pham chat, 3 nang luc chung, 7 nang luc dac thu candidates), the level-adaptive assessment rule (TT27 tieu hoc = remarks only, TT22 THCS/THPT = scores allowed), and the 'pham chat/nang luc declared in muc tieu must be named in at least one activity' quality check. Deliberately used loosely, not as a spec to follow literally (thatlq1812's explicit caveat, 2026-07-26) -- prior system's own orchestration machinery (persona/effort/token_budget/multi-turn sub-agent dispatch, Jinja2 profile placeholders, workspace-scan-before-work) was NOT ported; this skill is a single deterministic validator+renderer instead. Per thatlq1812 direction (2026-07-26), this tier deliberately skips prior system's bureaucratic-paperwork skills (annual_report/correspondence_log/directive_letter/meeting_minutes/school_decision/etc. -- Nghi dinh 30/2020 administrative templates) in favor of skills that serve the actual teaching/pedagogy work. v0.2.0 (2026-08-13) additionally references outside_research/references/anthropic-k12-teacher-skills's k12-lesson-planning skill (github.com/anthropics/k12-teacher-skills, Apache-2.0, co-developed Anthropic + Learning Commons, a real production skill in 'Claude for Teachers' -- a real deployed system for elicitation purposes, same standing as the prior-system citation above) for 3 concrete patterns adapted: (1) a clarify-priority-order section (what to ask the teacher first vs. infer/default) this SKILL.md previously lacked entirely; (2) an explicit copyright/originality guardrail (kien_thuc/noi_dung/san_pham/danh_gia inform scope from source material but must never paste SGK/textbook text verbatim), carried into both SKILL.md and assets/lesson_plan_template.json's own placeholder text; (3) a short 'presenting results to the teacher' UX note (treat warnings as double-check prompts, ask one explicit question before handing off to office-doc-creator) -- scaled down from the reference's full draft-first-offer/multi-artifact satisfaction-ask apparatus, since this skill produces one document via a deterministic script, not a conversational multi-artifact build. The reference's 'shared' JSON block (registering content once so multiple generated documents -- lesson plan + student materials + observation template -- cannot drift apart) was deliberately NOT adopted: this skill renders exactly one document from one JSON, so there is no multi-document drift problem to solve; adopting that architecture here would be unused abstraction, not a fix for a real gap. Investigating the adaptation surfaced a real, independent bug fixed this round: the validator accepted assets/lesson_plan_template.json's own unedited '<...>' placeholder text as valid non-empty content, so a plan with a forgotten field silently passed and rendered literal placeholder text into the KHBD -- verified reproducible before the fix, closed by validate_lesson_plan.py's new is_placeholder() check (exact-wrap-anchored, so it never flags real math content that legitimately uses '<'/'>' as inequality symbols)."
  version: 0.2.0
  grounding: required
  object_type: ["lesson-plan"]
---

# lesson-plan-builder

Validates a K-12 lesson plan (Kế hoạch bài dạy — KHBD) against the mandatory structure of Phụ lục IV, Công văn 5512/BGDĐT-GDTrH, then renders it to clean Markdown. Catches structural/vocabulary mistakes deterministically, before they reach a classroom.

## Why this skill, and why this scope

First skill for the **Teacher** audience tier (`docs/specs/STRATEGY_SPEC.md` §5.1), grounded in prior system's real previously-deployed `lesson_plan` skill — but used loosely per thatlq1812's explicit instruction, not copied as a spec ("dựa thôi chứ không phải tham khảo hẳn, vì tôi biết nó vẫn yếu"). prior system's SKILL.md packed in a large amount of harness-specific orchestration (persona/effort/token-budget tuning, batched sub-agent dispatch to avoid a specific timeout bug, Jinja2 profile placeholders, workspace-scan conventions) that is infrastructure for their own agent runtime, not domain knowledge — none of that was ported. What WAS worth keeping is the actual pedagogical/legal domain knowledge: the CV 5512 structure, the fixed CT GDPT 2018 competency vocabulary, and the level-adaptive assessment rule — real tacit knowledge elicited from a real deployed system, now encoded as a deterministic validator.

Per thatlq1812's direction (2026-07-26), the Teacher tier deliberately does **not** include prior system's bureaucratic-paperwork skills (annual reports, correspondence logs, directive letters, meeting minutes, school decisions — all Nghị định 30/2020 administrative templates). Those serve school-administration process, not the actual teaching work this tier is meant to serve.

## What CV 5512 requires (the domain knowledge this validator encodes)

- **Exactly 4 activities, fixed order, fixed names**: Khởi động → Hình thành kiến thức mới → Luyện tập → Vận dụng. Never reordered, renamed, merged, or split.
- **Each activity needs 4 sub-parts**: a) Mục tiêu, b) Nội dung, c) Sản phẩm, d) Tổ chức thực hiện — and (d) itself needs 4 steps: Chuyển giao nhiệm vụ → Thực hiện nhiệm vụ → Báo cáo, thảo luận → Kết luận, nhận định.
- **Mục tiêu uses a fixed 3-part structure**: kiến thức (free text) + năng lực (3 fixed năng lực chung + subject-specific năng lực đặc thù) + phẩm chất (fixed to exactly 5: Yêu nước, Nhân ái, Chăm chỉ, Trung thực, Trách nhiệm — from CT GDPT 2018, Thông tư 32/2018).
- **Level-adaptive assessment**: `khoi_lop` 1-5 (Tiểu học) → TT 27/2020 → remarks only, no scoring language allowed in `danh_gia`. `khoi_lop` 6-12 (THCS/THPT) → TT 22/2021 → scoring allowed.
- **Quality cross-check (not just form-filling)**: every phẩm chất/năng lực declared in `muc_tieu` should be named, by exact text, in at least one activity's own mục tiêu — otherwise it's a declared-but-undeveloped competency (a warning, not a hard error, since text matching is literal).

## Filling the JSON: what to ask first

The teacher (or an agent drafting alongside them) fills `assets/lesson_plan_template.json` before this validator ever runs — the script only checks completed content, it never asks a question itself. When helping draft the JSON, ask in this priority order and infer/default everything else silently:

1. **`khoi_lop`** — decides the TH-vs-THCS/THPT branch, which changes the allowed `danh_gia` language (TT27 vs TT22) and cannot be safely guessed.
2. **`mon_hoc` + `ten_bai`** — subject and topic drive every activity's content; nothing else can be drafted without them.
3. **`thoi_luong_phut` / `so_tiet`** — the total period length the 4 activities' minutes must sum to (the validator enforces a 5% tolerance).
4. **`muc_tieu.pham_chat` / `nang_luc_chung`** — pick from the fixed CT GDPT 2018 vocabulary above rather than asking the teacher to invent wording; only `nang_luc_dac_thu` (subject-specific) genuinely needs their input.
5. Everything else (activity content, `thiet_bi`, `danh_gia` wording) — draft from the above and let the validator's own errors/warnings catch anything still missing, mismatched, or left as unedited template text.

Don't interrogate the teacher for something the validator will catch on the next run anyway — ask only what's needed to unblock drafting.

## Content guardrail — write original content, never paste verbatim

`muc_tieu.kien_thuc`, each activity's `noi_dung`/`san_pham`, and `danh_gia` describe the lesson's own content and scope. Source material (SGK textbook, curriculum guides, sample lesson banks) may inform topic selection, scope, and sequencing — it must never be pasted into these fields verbatim. Write the lesson's own text in the teacher's or the drafting agent's own words.

`validate_lesson_plan.py` cannot mechanically verify originality against unknown source text — that stays a human/agent judgment call, same as pedagogy quality (see "What this skill does NOT do"). What it CAN and does check deterministically is the one guardrail failure that's actually detectable without a source corpus: a field still holding `assets/lesson_plan_template.json`'s own unedited `<...>` placeholder text (see "Known limitations").

## Run

```bash
python scripts/validate_lesson_plan.py <plan.json> [--render plan.md]
```

Start from `assets/lesson_plan_template.json`. Exit 0 = structurally valid (warnings may still print — read them, they're pedagogical quality signals), exit 1 = errors block (printed with field-level detail), exit 2 = malformed input. `--render` only writes output when there are zero errors.

## Presenting results to the teacher

This script is deterministic and silent by design — it never talks to the teacher itself; the calling agent does. Treat WARNINGS as prompts to double-check with the teacher (a competency cross-reference, a time-allocation drift, an unrecognized `nang_luc_dac_thu`), not as blocking findings — they're pedagogical quality signals, not errors. After a clean `--render`, say plainly what was produced (the KHBD) and ask one explicit question — whether they want any changes before handing it to `office-doc-creator` for the official `.docx` — rather than a bare "let me know if anything's wrong."

## What this skill does NOT do

- Doesn't judge pedagogy quality, content accuracy, or whether the activities are actually good teaching — pure structural/vocabulary/cross-reference validation.
- Doesn't generate the lesson content itself (no LLM/AI call) — the teacher (or the agent working with the teacher) fills the JSON; this only checks it.
- Doesn't produce a `.docx` in the official Times New Roman 14 / 2.5-2.0-2.0-2.0cm margin format — delegate that formatting step to `office-doc-creator` once the Markdown passes validation.
- Doesn't cover any of the administrative-paperwork document types (reports, decisions, correspondence logs, meeting minutes) — deliberately out of scope for this tier, see "Why this skill" above.

## Chains into `lesson-differentiation-builder`

When a validated lesson here needs to be adapted into below/at/above proficiency tiers for students at different levels, summarize this plan's `ten_bai`/`muc_tieu.kien_thuc` into `lesson-differentiation-builder`'s `source_lesson_summary` field (`skills/education/lesson-differentiation-builder/`) rather than re-describing the lesson from scratch. This chain is real but loose, not a strict pipe — the two skills use different field-naming conventions (this one's CV5512-grounded Vietnamese field names vs. the other's plain-English general-capability schema) and there is no automatic JSON handoff between them.

## Verified

v0.1.x: a real 4-activity THCS lesson plan (Toán, số nguyên tố) validated with zero errors/warnings and rendered correctly to Markdown; a Tiểu học (grade 3) plan with scoring language correctly errored citing TT27; a deliberately broken plan (wrong activity order, invalid phẩm chất/năng lực vocabulary, missing to_chuc_thuc_hien steps) correctly caught 7 errors + 3 cross-reference warnings; missing-fields and malformed-JSON cases correctly refused; a time-allocation mismatch (45 vs 90 declared minutes) correctly warned at the 5% tolerance threshold.

v0.2.0 re-verification (2026-08-13), 9 real runs: first reproduced the real gap this round's adaptation surfaced — running the unmodified validator against a plan with every field filled except `ten_bai` (left as the template's literal `<lesson/topic title>`) printed `VALID` and rendered `# Kế hoạch bài dạy: <lesson/topic title>` straight into the Markdown, exit 0. After adding `is_placeholder()`, the identical input now correctly errors (`ten_bai still contains unedited template placeholder text ('<lesson/topic title>')`), exit 1. Then re-ran the full regression set against the patched script: a fully-filled 4-activity THCS plan validated clean and rendered correctly; a plan whose content legitimately contains `<`/`>` as math inequality symbols ("x < 5 và y > 3") in `kien_thuc` and `noi_dung` correctly did NOT false-positive (exit 0, no placeholder error); the grade-3 TT27 scoring-language case, the wrong-order/invalid-vocabulary/missing-steps broken-structure case (8 errors + 2 cross-reference warnings), the time-allocation-deviation warning, missing-required-fields, malformed JSON, and the render-overwrite-without-`--force` refusal all reproduced their original v0.1.x behavior unchanged.

## Known limitations (v0.2.0)

- The "competency named in an activity" cross-check is literal substring matching — a teacher who paraphrases a competency name instead of using it verbatim will get a spurious warning. Read warnings as prompts to double-check, not infallible findings.
- `nang_luc_dac_thu` is only soft-validated (warns if outside the 7-item CT GDPT 2018 reference list) since subject-specific competency names legitimately vary more than the fixed pham_chat/nang_luc_chung sets.
- No support yet for `theme_lesson_plan`-style multi-lesson themed units or `cross_subject_plan`-style interdisciplinary/STEM lesson plans (both real prior system variants) — this covers the single-lesson case only; a future version could add these as additional structure profiles if real use shows the need.
- The new `is_placeholder()` check only catches a field whose ENTIRE value is still wrapped in `<...>` (the bundled template's own placeholder style) — it does not and cannot catch other unfilled-content patterns (a bare "TODO", an empty-looking single space, or text that IS original but happens to be low-quality). It's a mechanical completeness check, not a content-quality or originality check — see "Content guardrail" above for why originality itself stays a human/agent judgment call.
- The copyright/originality guardrail (see above) is documentation + one mechanical proxy check only — this skill has no source corpus to diff against, so it cannot detect a teacher pasting real SGK/textbook text that isn't template placeholder text. Enforcement relies on the calling agent and teacher following the stated guardrail.
