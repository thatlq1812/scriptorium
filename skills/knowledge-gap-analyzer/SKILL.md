---
name: knowledge-gap-analyzer
description: Flags skills below a caller-declared confidence threshold (or never self-assessed at all) that are required for a caller-declared target role, given a caller-declared self-assessment of skill x confidence-level pairs. `--json` output chains directly into `upskilling-roadmap-builder`'s `from_gap_analysis.py` to turn this diagnostic into an actionable day-by-day schedule. Use when a professional wants to know exactly which of a target role's required skills their own self-assessment doesn't yet clear a stated confidence bar. Do NOT use this to generate a confidence score, assess a person's actual competence, or invent a scoring methodology -- confidence values are always caller-supplied input, never computed, inferred, or estimated by this skill.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29).
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Lifelong Learner / Upskilling Professional role-capability tier (general-capability, public-source grounding per CLAUDE.md principle 4). Self-assessed-confidence-against-required-competency shape is standard, publicly documented career-development/L&D practice (e.g. competency self-assessment matrices used in individual development plans, and O*NET-style skills-gap comparison of a worker's self-rated skill profile against an occupation's required skill profile). The 1-5 ordinal confidence scale mirrors common self-assessment rubric conventions (novice-to-expert style Likert scales widely used in competency frameworks) but this skill treats it as a plain caller-supplied ordinal number, not a scoring methodology of its own -- no expert interview needed for this general-capability tier; the comparison logic itself is original to this session."
  version: 0.1.1
  changelog_0_1_1: "Doc-only: documented the deliberate chaining relationship with upskilling-roadmap-builder's new from_gap_analysis.py (2026-07-29, docs/DECISIONS_PENDING.md resolved item 8) -- no script/behavior change in this skill."
  grounding: not_applicable
  object_type: ["self-assessment", "skills-gap"]
---

# knowledge-gap-analyzer

Compares a caller-declared self-assessment against a caller-declared target-role skill requirement list, flagging every required skill below a caller-declared confidence threshold (or never assessed at all). Pure comparison -- it never scores, infers, or estimates confidence itself.

## Why this skill, and why this scope

For the **Lifelong Learner / Upskilling Professional** tier, self-assessment-against-requirements is a standard, publicly documented career-development technique (individual development plans, competency self-assessment matrices). This skill deliberately never generates a confidence value or interprets what a given confidence number "means" -- both the self-assessment's `{name, confidence}` pairs and the target role's required-skill list are always caller-supplied. The only judgment call this script makes is a numeric comparison (`confidence < threshold` and "was this skill assessed at all"), which is exactly the kind of thing CLAUDE.md's deterministic-first principle says a script should decide, not a model.

## Run

```bash
python scripts/analyze_knowledge_gap.py <self_assessment.json> <target_requirements.json> --threshold N [--output report.md] [--json]
```

Start from `assets/self_assessment_template.json` (`skills`: list of `{name, confidence}`, confidence integer 1-5) and `assets/target_requirements_template.json` (`target_role` string, `required_skills`: flat list of skill-name strings). `--threshold` (required, integer 1-5) is the minimum confidence a required skill's self-assessment must meet to count as "meets bar." Matching between a required skill's name and a self-assessment entry is exact (case-insensitive, whitespace-normalized) string equality -- no fuzzy matching.

A required skill absent from the self-assessment entirely is flagged as "never self-assessed", reported separately from "below threshold" so the two cases (assessed-but-low vs. never-assessed) aren't conflated. Output is a Markdown report (meets-bar / below-threshold / never-assessed sections) by default; `--json` prints the raw report instead.

**Chains into `upskilling-roadmap-builder`** (2026-07-29, `docs/DECISIONS_PENDING.md` resolved item 8): pipe `--json` output into `upskilling-roadmap-builder/scripts/from_gap_analysis.py` to turn this diagnostic report into an actual day-by-day schedule. This skill deliberately stops at the report — it never sequences anything, since scheduling is a distinct concern already solved by `study-plan-builder`'s algorithm, which `upskilling-roadmap-builder` reuses.

Exit codes: 0 = every required skill is self-assessed at/above threshold, 1 = well-formed input but at least one required skill is below threshold or was never assessed -- gaps flagged, not a crash, 2 = malformed input (bad JSON, missing/invalid fields, duplicate skill name in either file, out-of-range confidence, out-of-range `--threshold`).

## What this skill does NOT do

- Never computes, infers, or estimates a confidence value -- every confidence number comes directly from the caller-supplied `self_assessment.json`; this skill only compares numbers the caller already provided.
- Doesn't invent a confidence-scoring methodology or interpret what a given number "means" beyond ordinal comparison -- the 1-5 scale's real-world meaning is entirely up to the caller.
- Doesn't do fuzzy/semantic skill-name matching -- exact (case-insensitive, whitespace-trimmed) string equality only, same discipline as `upskilling-roadmap-builder`'s gap matching and `personal-profile-manager`'s `autofill.py`.
- Doesn't decide what skills a target role actually requires -- `required_skills` is always caller-supplied; this skill never researches or infers a role's real requirements.
- Doesn't call any LLM/AI API -- pure stdlib comparison and JSON I/O.

## Verified

Real 5-required-skill case against a self-assessment covering 4 of them (one below, three meeting, one missing entirely) at `--threshold 3`: correctly split into `meets_bar` (3 skills), `below_threshold` (1 skill, confidence 2), `not_assessed` (1 skill), exit 1, gap count 2. Full-pass case (all required skills present and at/above threshold) correctly reported "NO GAPS", exit 0. `--threshold 5` (maximum) case against skills at confidence 4 correctly flagged all of them as below-threshold. `--threshold 1` (minimum) case correctly passed every assessed skill regardless of confidence value (still flagged the unassessed one). Malformed-input cases all correctly refused with exit 2: `self_assessment.json` with confidence 0 and confidence 6 (both out of 1-5 range), a duplicate skill name in `skills` (case-insensitive), `target_requirements.json` missing `target_role`, `required_skills: []` (empty list), a duplicate entry in `required_skills`, and `--threshold 6` / `--threshold 0` (both out of range). `--json` output verified to contain `target_role`, `meets_bar`, `below_threshold`, `not_assessed`, `gap_count`, `ready` with correct values.

## Known limitations (v0.1.1)

- Exact-match-only skill-name comparison (see above) -- a self-assessment entry named differently from the target requirement's exact wording (e.g. "Excel" vs "Microsoft Excel") will be treated as never-assessed, not silently matched.
- No support for per-skill thresholds -- `--threshold` is a single global bar applied to every required skill in one run; a caller wanting different bars per skill must run this script multiple times with filtered input files.
- No time-decay or staleness handling on the self-assessment (e.g. a confidence value from a year-old assessment is treated identically to one from today) -- the caller is responsible for supplying a current self-assessment.
- No aggregate "how far below the bar" severity ranking beyond listing the raw confidence value next to the threshold -- the caller/downstream tool decides how to prioritize the flagged gaps.
