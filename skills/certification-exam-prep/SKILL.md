---
name: certification-exam-prep
description: Deterministic exam-readiness checklist validator -- checks a caller-declared study log's covered topics against a caller-declared certification exam blueprint's domain/objective list and flags every uncovered objective plus per-domain and overall coverage percentages. Use when a professional preparing for a real certification wants to know exactly which published exam objectives their study log hasn't covered yet. Do NOT use this to generate, guess, or assert real exam questions or a certification's real content -- the blueprint (domains, objectives, weightings) is always caller-supplied and any bundled example must cite the real certification body's own published exam guide.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29).'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Lifelong Learner / Upskilling Professional role-capability tier (general-capability, public-source grounding per CLAUDE.md principle 4). Checklist-against-published-blueprint shape is standard certification-prep practice publicly documented by certification bodies themselves (e.g. exam guides published by AWS, CompTIA, PMI, ISC2 that list weighted domains and testable objectives, which candidates are directed to self-check against). The bundled fixture (assets/exam_blueprint_template.json) cites AWS's own published exam guide for AWS Certified Cloud Practitioner (CLF-C02) at aws.amazon.com/certification/certified-cloud-practitioner/ for domain names and weightings; objective wording in the fixture is explicitly marked paraphrased/illustrative, not verbatim, per the fixture's own 'source_citation' field -- callers must supply the live official wording for real use. No expert interview needed for this general-capability tier; the validator logic itself (exact-match coverage checking) is original to this session."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["exam-blueprint", "study-log"]
---

# certification-exam-prep

Checks a study log's covered topics against a certification exam blueprint's domain/objective list. Pure checklist matching -- it never asserts, generates, or guesses real exam content.

## Why this skill, and why this scope

For the **Lifelong Learner / Upskilling Professional** tier, real professional certifications (cloud, security, PM, etc.) publish their own exam blueprints/objective lists directly (AWS, CompTIA, PMI, ISC2, and similar bodies all publish official exam guides). This skill never re-derives or invents that content -- it's a pure validator: the caller supplies the blueprint (ideally the exact current wording from the certification body's own published guide, with a citation) and their own study log, and the script does deterministic exact-match coverage checking. This keeps the skill entirely on the "checklist mechanics" side of the line, never the "what's actually on this exam" side, which this repo has no authority to assert and would risk becoming stale/wrong the moment a real exam blueprint version changes.

## Run

```bash
python scripts/check_exam_readiness.py <blueprint.json> <study_log.json> [--threshold-percent 100] [--output report.md] [--json]
```

Start from `assets/exam_blueprint_template.json` (`certification_name`, `source_citation` -- must name the real certification body's published exam guide -- and `domains`, each with `domain_name`, `weight_percent`, and a non-empty `objectives` list) and `assets/study_log_template.json` (`topics_covered`, a flat list of strings). Matching is exact (case-insensitive, whitespace-normalized) string equality between an objective's text and a study-log entry -- no fuzzy/semantic matching.

`--threshold-percent` (default 100) is the minimum per-domain coverage percent required to count as "ready". Output is a Markdown report (per-domain coverage table, uncovered-objectives checklist per domain, and any study-log topics that didn't match any objective) by default; `--json` prints the raw report instead.

Exit codes: 0 = every domain at/above threshold (exam-ready), 1 = well-formed input but at least one domain (or the overall total) below threshold -- gaps flagged, not a crash, 2 = malformed input (bad JSON, missing `source_citation`, empty domain/objectives lists, duplicate objective text across the blueprint, out-of-range `weight_percent`, invalid `--threshold-percent`).

## What this skill does NOT do

- Never asserts, fabricates, or guesses real exam questions or a certification's actual current content -- the blueprint is always caller-supplied; the bundled fixture only illustrates the checklist mechanics, with an explicit disclaimer that its objective wording is paraphrased, not the live verbatim text.
- Doesn't do fuzzy/semantic matching between study-log wording and objective wording -- an exact-text mismatch is reported as uncovered, not silently resolved by guessing the caller "probably meant" the matching objective.
- Doesn't validate that the domains' `weight_percent` values sum to 100 -- weightings are recorded and reported per-domain but the script doesn't enforce a total (a blueprint might legitimately omit some domains from a partial study-log check).
- Doesn't track study time, difficulty, or confidence -- purely "was this objective's exact text logged as covered, yes or no."
- Doesn't call any LLM/AI API -- pure stdlib string comparison and arithmetic.

## Verified

Bundled fixture (AWS CLF-C02, 4 domains, 14 objectives total) against bundled `study_log_template.json` (4 topics covered): correctly computed per-domain coverage (Cloud Concepts 2/3=66.67%, Security and Compliance 1/4=25%, Cloud Technology and Services 0/4=0%, Billing 1/3=33.33%), overall 4/14=28.57%, correctly refused as NOT READY at default `--threshold-percent 100` (exit 1), correctly listed every uncovered objective per domain. Full-coverage case (study log containing all 14 fixture objectives verbatim) correctly reported READY (exit 0), overall 100%. `--threshold-percent 0` case correctly always READY regardless of coverage (exit 0). Malformed-input cases all correctly refused with exit 2: missing `source_citation`, `domains` present but empty list, a domain with `weight_percent` 150 (out of range), duplicate objective text across two different domains, `topics_covered` containing a non-string entry, and a study log with `topics_covered: []`. `--json` output verified to contain `overall_coverage_percent`, `ready`, `domains[].uncovered_objectives`, and `unmatched_study_log_topics` with correct values.

## Known limitations (v0.1.0)

- Exact-match-only comparison (see above) is the single biggest practical limitation -- a learner who logs "shared responsibility model" instead of the blueprint's exact "Describe the AWS shared responsibility model" will show that objective as uncovered even though they likely studied it. This is a deliberate "never guess" choice, not an oversight; a future version could add an explicit caller-declared alias/synonym map (never an automatic fuzzy matcher) if real use shows the friction matters.
- Bundled fixture's objective wording is paraphrased/illustrative (explicitly disclaimed in its own `source_citation` field), not verified verbatim against the live AWS exam guide PDF at the time of writing -- real use must swap in the caller's own current, verbatim objective text.
- No support for objectives that only partially overlap in wording across domains (each objective's normalized text must be globally unique in the blueprint, enforced as a malformed-input error) -- a legitimately reused sub-objective phrase across two domains must be worded distinctly by the caller.
- No per-objective weighting within a domain (only domain-level `weight_percent`) -- coverage percent within a domain treats every objective in that domain as equally important.
