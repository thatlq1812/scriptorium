# Cluster Survey Template

| Version | Date | Author | Description |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-27 | Claude | First version, distilled from real experience running `outside_research/research_01_survey.md` (the Legal cluster's real practitioner survey) through the full pipeline. See "Lessons this template encodes" below for what specifically changed and why. |

---

## Purpose

The standard survey shape for eliciting a new audience-tier or specializer-network cluster (principle 4, `docs/specs/STRATEGY_SPEC.md` §7 — never let `skill-creator` run from a self-generated guess, always start from a real elicited source). Copy this file to `outside_research/research_NN/research_NN_survey.md`, fill it with a real respondent (a practitioner, a teacher, a student — someone who actually does the work), then follow the same distillation path `research_01_survey.md` took: survey → consolidation survey (group raw items into skill candidates, in `docs/ROADMAP.md`) → `skill-creator`.

A survey filled out by guessing what a respondent *might* say is not a survey — it is exactly the self-generated-input problem principle 4 exists to prevent. If a real respondent isn't available yet, that is a real gap to state plainly (see how `outside_research/research_02/research_02_result_01.md` handled it for Student/K12), not a reason to fill this template in yourself.

## Lessons this template encodes

Distilled from what actually happened when `research_01_survey.md`'s answers were turned into 5 real skills:

1. **The free-text caveat column did more work than the structured columns.** The respondent's own hedges — *"Tự động cập nhật khi văn bản sửa đổi... (Maybe nhưng hơi khó vì VBPL thay đổi liên tục)"*, *"Dựa theo nguồn 100%, không tự generate thông tin mới"* — became the literal, load-bearing scope boundary for `legal-citation-checker` (refuses hiệu lực verification) and `legal-research-brief`/`document-ai-structurer` (hard grounding requirement). Keep this column free-text and genuinely optional to leave blank — a forced-choice field would have lost this.
2. **What was missing, and had to be reconstructed by the building agent afterward instead of asked upfront**: whether a real data source/checklist/database exists for the task (this took an entire session of investigation for `legal-form-filler`'s "form suggestion" gap that a single survey question would have surfaced immediately), how often the task actually comes up (no way to prioritize the 11 raw items against each other without this), and what the respondent does today without AI (reveals existing checklists/templates that can become real caller-supplied assets, the same way `office-doc-creator`/`legal-form-filler` expect a template to already exist). This template adds explicit columns for all three.
3. **Grouping by broad category (I, II, III...) genuinely helped** — it's what let 11 raw items consolidate into 5 skills instead of 11, avoiding the fragmentation EduStation's 63-folder survey later confirmed was a real anti-pattern. Keep the category grouping.

## How to run a survey session

1. Open with the same framing question `research_01_survey.md` used, adapted to the audience: **"What steps of your work currently repeat, and what would you want an assistant to actually do for you?"** — anchored in real repetitive pain, not a feature wishlist.
2. Let the respondent talk/write freely first; only impose the table structure when writing it down. Forcing the table live tends to flatten the caveats that turned out to matter most (lesson 1 above).
3. Every item needs a category (roman numeral, freely chosen per cluster — don't force-fit into Legal's 5 categories for a different domain).
4. Do not edit or "clean up" a respondent's caveats/hedges once written — verbatim is the point; a caveat rewritten to sound more confident is a caveat with the useful part removed.

## Template

**Topic:** *[The framing question — see step 1 above]*

**Respondent:** *[Real name/role, or an anonymized description if the respondent asked for that — never invented]*

**Date:** *[YYYY-MM-DD]*

| STT | Hạng mục | Mô tả chi tiết | Tần suất | Dữ liệu/checklist sẵn có? | Rủi ro nếu AI làm sai | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| **I. [Category name]** | | | | | | |
| 1 | *[short label]* | *[what repeats, what they'd want done]* | *[e.g. daily / weekly / per-case]* | *[a real template/checklist/database they already use today, or "none" — never guessed]* | *[what happens if the output is wrong — informs risk_tier later]* | *[free text — hedges, exceptions, "this is hard because...", anything unprompted]* |
| 2 | | | | | | |
| **II. [Category name]** | | | | | | |
| 3 | | | | | | |

## Column reference (why each one exists)

- **Hạng mục / Mô tả chi tiết** — same as `research_01_survey.md`'s original 2 columns, unchanged; this is the core ask.
- **Tần suất** — new (lesson 2). Feeds prioritization when consolidating raw items into skills (`docs/ROADMAP.md`'s consolidation-survey step) — a daily pain point outranks a once-a-year one, all else equal.
- **Dữ liệu/checklist sẵn có?** — new (lesson 2). Directly answers the question that took a full session to reconstruct for `legal-form-filler`. If the answer is "none," that is itself the finding — the resulting skill should say so explicitly (`grade-book-builder`'s refusal to hardcode TT22/2021 weights is the model to follow), not invent a source.
- **Rủi ro nếu AI làm sai** — new (lesson 2). Direct input to `registry/SCHEMA.md`'s `risk_tier` field (N1-N5) once a skill is built — skip re-deriving this from scratch per skill the way every cluster so far has had to.
- **Ghi chú** — unchanged, deliberately free-text and optional (lesson 1). The single highest-value column based on real outcomes — protect it from being replaced with a dropdown or forced structure.

## After the survey: what happens next

Same path every prior cluster took, not a new process:

1. **Consolidation survey** — group raw items into candidate skills (not 1:1), checking `registry/skills.json` first for ≥80% overlap with something that already exists (dedup-novelty-check principle, `registry/SCHEMA.md`). Record in `docs/ROADMAP.md`.
2. **`skill-creator`** runs from the consolidated candidates + this survey as the elicited source.
3. Real data gaps found along the way (a "Dữ liệu/checklist sẵn có?" answer of "none," or a risk/regulation question with no free API) get flagged as an explicit out-of-scope boundary in the resulting skill's `SKILL.md`, the same way `legal-citation-checker` and `legal-form-filler` did — never filled in with an invented answer.
