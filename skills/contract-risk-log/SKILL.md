---
name: contract-risk-log
description: Validates a structured contract risk-review log — every flagged issue must name a clause, a concern, a specific (not vague) recommended action, a severity, and a category; the log must explicitly state whether a systematic review actually found zero issues or simply wasn't done. Use after a human/agent reviews a contract for risk, to make sure the findings are logged completely and traceably before going to a client or decision-maker. Do NOT use this to automatically detect contract risk — identifying whether a clause is actually risky requires legal judgment this skill does not attempt; it only checks that a human/agent-authored risk assessment is structurally complete.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-26) — the bundled template initially warned about an internal inconsistency in its own example data (an issue's clause wasn't listed as reviewed), fixed and re-verified clean; an ambiguous empty-issues-with-no-flag case, a contradictory no-issues-flag-with-nonzero-issues case, an invalid severity value, and a duplicate issue id were all correctly refused; a vague recommended action ("review this") correctly warned without blocking; an explicit "reviewed, found nothing" case correctly passed; malformed JSON correctly refused (exit 2).
metadata:
  domain: legal
  task_type: review-qa
  risk_tier: N3
  source: self-authored
  elicited_from: "Elicited from survey item 6 (outside_research/research_01_survey.md: 'Rà soát hợp đồng — phân tích các điều khoản của hợp đồng, phát hiện điều khoản bất lợi, thiếu nội dung hoặc chưa phù hợp với quy định pháp luật; đề xuất phương án sửa đổi'). Deliberately does NOT attempt automated risk *detection* -- identifying a clause as legally risky is a judgment call this project's principles (never let an agent claim certainty it can't deterministically back) explicitly guard against automating past what's checkable. Instead structured as a completeness/consistency validator over a human-or-agent-authored risk log, directly mirroring the pattern already proven in this repo's peer-review skill (validate_claim_evidence.py: 'reports IDs and counts, not claim text' -- a structural check on analysis, not a substitute for it). The explicit-not-ambiguous no-issues-found requirement is a new pattern for this project, added because a silently-empty issues list in a legal risk log is a genuinely dangerous ambiguity (did the reviewer check and find nothing, or not review at all?)."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["contract", "risk-log"]
---

# contract-risk-log

Validates that a contract risk-review log is structurally complete and internally consistent. Never detects risk itself — that stays a human/agent judgment call, this only checks the findings were logged properly.

## Why this skill, and why this scope

Survey item 6 asks for automated detection of "điều khoản bất lợi" (unfavorable clauses) — but deciding whether a clause is actually legally risky requires real legal judgment that cannot be deterministically automated without producing false confidence. This project's established pattern for exactly this situation is `peer-review`'s claim-evidence matrix: don't automate the judgment, structure and validate the *log* of the judgment instead. Applied here: a human or LLM-driven review process identifies issues; this skill only checks that every identified issue is logged completely (clause, concern, category, severity, a *specific* recommended action) and that the log is honest about whether "no issues" means "reviewed and clean" or "not actually reviewed."

## What this skill checks

1. **Required log metadata**: contract title, reviewer, review date, and a non-empty `clauses_reviewed` list (proves a systematic pass happened, not an ad-hoc glance).
2. **Explicit no-issues state**: an empty `issues` list requires `no_issues_found_after_review: true` — a silently-empty list is a dangerous ambiguity in a risk log (did the reviewer find nothing, or just not finish?). The reverse (the flag set true with a non-empty issues list) is also refused as contradictory.
3. **Per-issue completeness**: `id` (unique), `clause_location`, `risk_category`, `severity` (`low`/`medium`/`high`), `concern`, and `recommended_action` are all required. A `recommended_action` that's just "review this"/"TBD"/similarly vague is warned (not blocked) — a real quality signal, since a risk log entry that doesn't say *what to do* isn't actionable.
4. **Cross-check**: an issue's `clause_location` should be in the declared `clauses_reviewed` list — warns if not (was this clause actually part of the systematic pass, or found some other way?).

## Run

```bash
python scripts/validate_risk_log.py <risk_log.json> [--render risk_log.md]
```

Start from `assets/risk_log_template.json`. Exit 0 = structurally complete (warnings may still print), 1 = errors block, 2 = malformed input. `--render` only writes after zero errors.

## What this skill does NOT do

- Doesn't detect contract risk automatically — no clause-content analysis, no LLM call, no pattern-matching against "risky clause" templates. A human or another process must identify the issues; this only validates the log of them.
- Doesn't assess whether a `recommended_action` is legally sound — only that it's present and not obviously a placeholder.
- Doesn't check clause text for mechanical errors (numbering, cross-references, party names) — that's `contract-consistency-linter`'s job, a separate concern from risk assessment.
- Doesn't render the final client-facing report — delegate to `office-doc-creator` once the log passes validation.

## Known limitations (v0.1.0)

- `risk_category` has a soft (warning-only) fixed vocabulary — a category outside the known set is flagged but not blocked, since real contracts surface categories this list won't anticipate.
- The vague-`recommended_action` check is a small hand-curated phrase list ("review this," "TBD," etc.) — it will miss most genuinely vague actions phrased differently; it's a narrow safety net, not a quality guarantee.
- No severity-weighted summary or prioritization output in v0.1.0 — the log is a flat list; a future version could add a severity-sorted rendering if real use shows the need.
