---
name: dissertation-proposal-scaffold
description: Validates a Master's/PhD dissertation-proposal document has the five standard required sections — problem statement, literature gap, research questions, methodology, timeline — each non-empty (a blank/placeholder section, an empty research-questions list, or a timeline milestone missing its target date is a hard error naming the exact missing piece), then renders a clean Markdown scaffold. Use when drafting or checking a thesis/dissertation proposal's structure before submitting it to an advisor or committee. Do NOT use this to judge whether the problem is significant, the literature gap is real, the research questions are answerable, or the methodology is sound — it validates document structure/completeness only, never intellectual content.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in the standard graduate research-proposal structure taught broadly across research-methods literature and university Graduate College proposal guidelines: problem statement, review of the literature identifying a gap, research questions (or hypotheses), methodology, and a timeline/work plan -- the same five-part shape described in widely-used graduate methods texts such as Creswell & Creswell, 'Research Design: Qualitative, Quantitative, and Mixed Methods Approaches' (SAGE, latest editions), and mirrored across public university thesis/dissertation-proposal guideline pages (problem statement -> literature review/significance -> research questions -> methodology -> timeline). This is public, widely-taught convention, not a niche tacit process, matching this project's general-capability elicitation tier (CLAUDE.md principle 4) -- no expert interview needed. The structural-completeness validator shape (every required section must be present and non-empty, named exactly when missing) mirrors skills/legal/legal-research-brief/scripts/validate_legal_brief.py's completeness check, adapted from a 7-section legal-brief structure to this 5-section academic-proposal structure -- unlike legal-research-brief, this skill has no per-claim source-citation requirement, since a proposal's required sections are a fixed document-structure check, not a claim-by-claim grounding check."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["dissertation-proposal"]
---

# dissertation-proposal-scaffold

Validates that a Master's/PhD dissertation-proposal document has all five standard required sections, each non-empty, then renders it to a clean Markdown scaffold. Never judges the intellectual quality of the content — structural completeness only.

## Why this skill, and why this scope

A graduate student drafting a thesis/dissertation proposal needs the document to actually contain every section an advisor/committee expects before it's worth a substantive read: a stated problem, an identified gap in the literature, concrete research questions, a methodology, and a timeline. This five-part shape is standard, publicly documented graduate-research convention (Creswell's widely-used research-design texts, and the same structure mirrored across public university Graduate College proposal-guideline pages) — general-capability tier per CLAUDE.md principle 4, no expert interview needed.

The validator shape (every required section present and non-empty, named exactly when missing, --render only on a clean pass) mirrors `legal-research-brief`'s structural-completeness check, adapted from its 7-section legal-brief structure to this 5-section academic-proposal structure. Unlike `legal-research-brief`, this skill does not require per-claim source citations — a proposal's required sections are a fixed document-structure check, not a claim-by-claim grounding check, so `grounding` is `not_applicable` here (same as `competency-rubric-builder`'s stance on its own purely structural check).

## The 5 required sections this skill encodes

| Section | Requirement |
| --- | --- |
| `problem_statement` | Non-empty string |
| `literature_gap` | Non-empty string |
| `research_questions` | Non-empty list; every item a non-empty string |
| `methodology` | Non-empty string |
| `timeline` | Non-empty list of milestones; every milestone has non-empty `milestone` and `target_date` |

`title` is also required. `degree_level` is accepted and rendered if present but not validated against a fixed vocabulary (a proposal may legitimately be for a Master's thesis, PhD dissertation, or another program-specific label).

## Run

```bash
python scripts/validate_proposal.py <proposal.json> [--render proposal.md] [--force]
```

Start from `assets/proposal_template.json` (a valid PhD proposal example — read it for the exact JSON shape). Exit 0 = all 5 sections present and non-empty, exit 1 = errors block (each naming the exact missing/empty field, including the exact list index for a bad `research_questions` or `timeline` entry), exit 2 = malformed input, or `--render` target already exists without `--force`. `--render` only writes output when there are zero errors.

## What this skill does NOT do

- Doesn't judge whether the problem statement is actually significant, whether the literature gap is real (vs. a gap the student simply didn't find), whether the research questions are answerable, or whether the methodology is sound for the questions asked — pure structural/completeness validation, content quality is always a human (advisor/committee) judgment.
- Doesn't check citation formatting or verify that literature cited in `literature_gap` actually exists — no source-grounding requirement in this skill (contrast `legal-research-brief`, which does require per-claim citation to a declared source; a proposal's literature gap is prose, not a list of individually-cited claims).
- Doesn't generate proposal content itself (no LLM/AI call) — the student (or the agent working with them) writes the JSON; this only checks it.
- Doesn't produce the final formatted `.docx`/`.pdf` in a specific university's required proposal template — delegate that formatting step to `office-doc-creator` once the Markdown passes validation.
- Doesn't validate against any specific program's additional required sections (e.g. some programs require a separate "significance" or "limitations" section) — this validates the 5-section shape common across the public research-methods literature this skill is elicited from, not a specific institution's exact template.

## Verified

The bundled valid PhD proposal (2 research questions, 4 timeline milestones) validated with zero errors and rendered correctly to Markdown with all 5 sections plus title/degree level. Deliberately broken cases: a proposal with an empty `problem_statement`, an empty `research_questions` list, and an empty `timeline` list correctly refused all 3 issues by exact field name in one run; a `timeline` with one milestone missing `target_date`, one missing `milestone`, and one non-object entry correctly refused all 3 by exact index/field; malformed (non-JSON) input correctly refused with exit 2; `--render` correctly refused to overwrite an existing file without `--force` (exit 2) and succeeded with `--force` (exit 0).

## Known limitations (v0.1.0)

- Presence/non-emptiness only — a `problem_statement` of a single word ("TBD") passes structurally even though it is not a real problem statement; content quality is entirely out of scope.
- No cross-check between sections (e.g. verifying a `research_questions` entry is actually addressed by the stated `methodology`) — each section is validated independently, not for mutual consistency.
- `degree_level` is accepted/rendered but never validated against a fixed vocabulary, since program-specific degree labels vary too widely to hardcode a reference list, the same reasoning `competency-rubric-builder` gives for not validating its own `khoi_lop` field against a fixed framework.
- Only the 5-section shape common across the general public research-methods literature is checked — a specific university's proposal template with additional required sections (e.g. a separate ethics/IRB section) will pass this validator even if it's missing a section that specific institution requires.
