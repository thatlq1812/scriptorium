---
name: contract-risk-log
description: Validates a structured contract risk-review log — every flagged issue must name a clause, a concern, a specific (not vague) recommended action, a severity, and a category; the log must state whether a systematic review found zero issues or simply wasn't done. Also validates a batch/tabular review of N contracts against the same M review columns (a due-diligence pass across several agreements) — every document x column cell must be a value with a verbatim quote + location, "not_present", or "needs_review" with a reason; a missing cell is refused, never silently blank. Use after reviewing one contract for risk (single-log mode) or several contracts against a shared checklist (batch mode). Do NOT use this to automatically detect contract risk or extract clause values — that requires legal judgment this skill does not attempt; it only checks a human/agent-authored assessment is structurally complete and grounded.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-26). See "Verified" section below for real test-case detail.'
metadata:
  domain: legal
  task_type: review-qa
  risk_tier: N3
  source: self-authored
  elicited_from: "Elicited from survey item 6 (outside_research/research_01_survey.md: 'Rà soát hợp đồng — phân tích các điều khoản của hợp đồng, phát hiện điều khoản bất lợi, thiếu nội dung hoặc chưa phù hợp với quy định pháp luật; đề xuất phương án sửa đổi'). Deliberately does NOT attempt automated risk *detection* -- identifying a clause as legally risky is a judgment call this project's principles (never let an agent claim certainty it can't deterministically back) explicitly guard against automating past what's checkable. Instead structured as a completeness/consistency validator over a human-or-agent-authored risk log, directly mirroring the pattern already proven in this repo's peer-review skill (validate_claim_evidence.py: 'reports IDs and counts, not claim text' -- a structural check on analysis, not a substitute for it). The explicit-not-ambiguous no-issues-found requirement is a new pattern for this project, added because a silently-empty issues list in a legal risk log is a genuinely dangerous ambiguity (did the reviewer check and find nothing, or not review at all?). v0.2.0's batch mode: thatlq1812 confirmed no real thatlq1812-supplied diligence schema exists to elicit from, and explicitly authorized building against a generic/common schema instead of blocking on it -- the 3-state (value/not_present/needs_review) + verbatim-quote-and-location discipline is adapted from a pattern found independently in claude-for-legal's tabular-review/claim-chart and lq-skills' case-file-analyzer (outside_research/research_03_legal-repo/, license varies per-skill, not redistributed -- only the schema shape reused, no code or content copied)."
  version: 0.2.0
  changelog_0_2_0: "Added scripts/batch_tabular_review.py: validates N documents x M caller-declared review columns in one pass. Every (document, column) pair must have exactly one cell; state='value' requires value+verbatim_quote+location (never an unverifiable bare claim); state='needs_review' requires a reason; a missing cell is refused, never silently absent. --render writes a Markdown table. Kept as a second script in this skill (not a new skill) since it's the same non-detection, structure-only-validation posture as validate_risk_log.py, just applied across multiple documents/columns instead of one contract's issue list."
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

## Batch/tabular mode — reviewing N contracts against the same checklist at once

```bash
python scripts/batch_tabular_review.py <batch_review.json> [--render batch_review.md] [--force]
```

Start from `assets/batch_tabular_review_template.json`. The caller declares `documents` (list) and `columns` (list, whatever review categories actually apply — no fixed vocabulary, since no real thatlq1812-supplied diligence schema was available to elicit one from). Every `(document, column)` pair needs exactly one cell in `cells`, each with a `state`:

- `"value"` — requires `value` (the finding), `verbatim_quote` (the exact source text), and `location` (e.g. "Điều 5"). A value with no quote to check it against is treated as an unverifiable claim, not a finding, and refused.
- `"not_present"` — the column genuinely doesn't apply to this document (e.g. no termination clause exists at all).
- `"needs_review"` — requires a `note` explaining why (illegible, ambiguous, conflicting) — never a bare "needs review" with no reason.

A cell for a `(document, column)` pair that was never declared in `cells` is refused (not silently treated as "not present") — this is the core discipline adapted from the outside-repo pattern this mode is inspired by: a batch review must account for every cell explicitly, the same way `contract-risk-log`'s single-log mode requires an explicit `no_issues_found_after_review` flag instead of silently accepting an empty list.

## What this skill does NOT do

- Doesn't detect contract risk automatically — no clause-content analysis, no LLM call, no pattern-matching against "risky clause" templates. A human or another process must identify the issues; this only validates the log of them.
- Doesn't assess whether a `recommended_action` is legally sound — only that it's present and not obviously a placeholder.
- Doesn't check clause text for mechanical errors (numbering, cross-references, party names) — that's `contract-consistency-linter`'s job, a separate concern from risk assessment.
- Doesn't render the final client-facing report — delegate to `office-doc-creator` once the log passes validation.
- (batch mode) Doesn't extract cell values from contract text itself — every `value`/`verbatim_quote`/`location` is supplied by whoever did the actual reading (human or agent); this only checks the resulting table is complete and each value is grounded in a quote.
- (batch mode) Doesn't decide which columns matter for a given review — no fixed/official diligence checklist is bundled (none was available to elicit from), the caller declares whatever categories their own real review needs.

## Verified

Single-log mode: the bundled template initially warned about an internal inconsistency in its own example data (an issue's clause wasn't listed as reviewed), fixed and re-verified clean; an ambiguous empty-issues-with-no-flag case, a contradictory no-issues-flag-with-nonzero-issues case, an invalid severity value, and a duplicate issue id were all correctly refused; a vague recommended action ("review this") correctly warned without blocking; an explicit "reviewed, found nothing" case correctly passed; malformed JSON correctly refused (exit 2).

Batch mode (2026-07-27): the bundled 2-document x 3-column template passed clean and rendered a correct Markdown table (including a `not_present` cell and a `needs_review` cell with its reason both displaying correctly). 7 deliberately broken cases each caught with the exact expected reason: a missing cell (removed from the template), a duplicate cell for the same document/column, a `"value"` cell missing `verbatim_quote`, a `"needs_review"` cell missing `note`, a duplicate document name, a cell referencing an undeclared column (correctly reported both the bad reference AND the resulting missing-cell gap it created), and malformed JSON (exit 2).

## Known limitations (v0.2.0)

- `risk_category` has a soft (warning-only) fixed vocabulary — a category outside the known set is flagged but not blocked, since real contracts surface categories this list won't anticipate.
- The vague-`recommended_action` check is a small hand-curated phrase list ("review this," "TBD," etc.) — it will miss most genuinely vague actions phrased differently; it's a narrow safety net, not a quality guarantee.
- No severity-weighted summary or prioritization output — the single-log mode's log is a flat list; a future version could add a severity-sorted rendering if real use shows the need.
- Batch mode has no severity/priority concept at all (unlike single-log mode) — a cell is just value/not_present/needs_review, no risk ranking. If real use needs risk-weighting across a batch, that's a real gap for a future version, not silently assumed unnecessary.
- Batch mode's schema is generic (adapted from an outside pattern, not elicited from a real thatlq1812-supplied diligence checklist) — if a real checklist becomes available later, this schema should be revisited against it rather than assumed already correct.
- Only verified against a small synthetic 2-document x 3-column batch this session — not yet exercised on a real multi-document diligence review.
