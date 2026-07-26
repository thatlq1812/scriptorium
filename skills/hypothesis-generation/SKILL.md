---
name: hypothesis-generation
description: Turns an observation into a transparent set of rival candidate hypotheses, discriminating predictions, and a preregistration-ready plan — never presenting any hypothesis as established fact. Use when moving from an observation/preliminary finding to a testable research plan, or when a draft is at risk of overclaiming causation/certainty. Do NOT use for patient-specific diagnosis, treatment, or clinical advice — this skill is a structured-thinking + drafting aid, not a scoring or decision system, and the accountable human always verifies the output.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, re, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean on Claude Code (2026-07-26, v0.2.0); the run evidence is in `metadata.verified_runs`. No other harness verified — do not add one without testing it directly.
metadata:
  domain: general
  task_type: research
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in K-Dense-AI/scientific-agent-skills hypothesis-generation (MIT, verified via gh api + per-folder license check 2026-07-26) for the object model (observation/hypothesis/prediction/estimand kept distinct), non-negotiable boundaries (never present a hypothesis as fact, no clinical claims, human-accountability gate, no auto-scoring), and the general workflow (freeze observation -> generate rivals -> derive discriminating predictions -> preregister). Rewritten from scratch and scoped down from the original's 7-script/9-reference-doc suite to the 3 highest-value, most general-purpose tools: a JSON schema validator enforcing the rivals+status-never-confirmed rules, a causal-claim language linter, and a preregistration-scaffold generator -- dropped format-specific validators (operationalization checklist, falsification/controls, evidence-ledger audit) as a v2+ extension if the need materializes."
  version: 0.2.0
  verified_runs: "2026-07-26, v0.2.0, Claude Code: a valid rival-pair record validated and generated a preregistration; a broken record (status=\"confirmed\", single candidate, self-contrast, missing accountable_human) was rejected by the validator AND refused by the preregistration generator with all 4 reasons, exit 1 — the case that silently produced a document in v0.1.0. Self-contrast and uncovered-candidate rules each verified on their own fixture. The causal-claim linter flagged proves/confirms (medium), \"first study to\"/\"no prior work exists\" (high) and \"due to\" (low), while correctly ignoring \"may cause\", a blockquoted overclaim, a fenced code block, and a line marked with the claim-ok suppression comment."
  changelog_0_2_0: "Closed the skill's central hole: generate_preregistration_scaffold.py ran on ANY record, so a record whose candidate was labeled status='confirmed', had no rival, and named no accountable human produced a clean-looking preregistration document -- the validator existed but nothing forced it, and the generator is what writes the artifact that gets shared. It is now gated on validate_hypothesis_schema.py with no bypass flag (mirroring how peer-review gates its own scaffold generator). Validator additions: a prediction may not list its own candidate in contrasted_with (contrasting a candidate with itself discriminates nothing), and every candidate must carry at least one prediction (the doc said 'for each candidate', the tool did not check it); --allow-class replaces the documented need to edit CANDIDATE_CLASSES in the script. Linter: severity levels + --fail-on, hedge-aware matching ('may cause' is not an overclaim), code fences/blockquotes skipped, `<!-- claim-ok -->` suppression, and new high-severity absence-claim patterns."
  risk_tier_note: "N2, not N1: even though the tooling is fully local/deterministic, the skill's SUBJECT MATTER (hypothesis framing) can influence downstream research/clinical decisions if used carelessly; the non-negotiable-boundaries section exists specifically to keep that risk bounded."
---

# hypothesis-generation

Turns an observation into a transparent set of candidate explanations and discriminating tests. A hypothesis is a proposal to be challenged, never a finding, fact, diagnosis, or recommendation.

## Non-negotiable boundaries

Before using unpublished, sensitive, personal, proprietary, or security-relevant material: confirm authorization, keep it local unless an authorized human explicitly approves an external destination, and stop at the appropriate human/ethics/regulatory gate. This skill never:

- presents a hypothesis, mechanism, or pattern as established evidence;
- claims novelty because a quick search found nothing (say "not located within the documented search boundary," never "no prior work exists");
- infers causation from association, temporal order alone, or predictive accuracy;
- supplies patient-specific diagnosis, treatment, dose, or prognosis;
- automatically scores, ranks, or selects a "winning" hypothesis — every tool here validates structure, not truth.

## Why this differs from the original K-Dense-AI skill

The source skill's object model and boundaries are excellent and entirely general-purpose (not biology-specific) — kept as-is. Its 7-script/9-reference-doc suite was scoped down to the 3 tools with the best value-to-complexity ratio for a v0.1.0: a schema validator, a causal-claim linter, and a preregistration-scaffold generator. Dropped: the operationalization checklist, falsification/controls checker, and evidence-ledger audit scripts — each is a reasonable v2+ addition if real use reveals the need, but were not ported to keep this initial harvest testable end-to-end in one session.

## Keep the objects distinct

**Observation** (what was measured) ≠ **Hypothesis** (a candidate explanation) ≠ **Prediction** (an observable implication, stated before checking) ≠ **Evidence** (what bears on a claim — never the claim itself). Do not collapse these. Rejecting one rival does not prove another true; unconsidered rivals remain possible.

## Workflow

### 1. Freeze the observation

Write what was measured/noticed — source, population, unit of observation, uncertainty, and whether the pattern was expected, exploratory, or noticed after viewing results — BEFORE interpreting it. Use "reported"/"observed"/"associated," not causal language, unless a causal design justifies it.

### 2. Generate rivals, not one explanation

For every observation worth investigating, generate at least 2 candidates from genuinely different explanatory classes (mechanism, measurement artifact, confounding, selection bias, reverse causation, temporal/boundary conditions, stochastic variation, competing mechanism). Fill `assets/hypothesis_record_template.json`.

```bash
python scripts/validate_hypothesis_schema.py record.json [--allow-class <name>]
```

Checks structural completeness: every candidate stays labeled `"status": "candidate"` (never `confirmed`/`proven`/`established`), at least 2 rivals exist, every candidate carries at least one prediction, every prediction references a real candidate and at least one **other** candidate it discriminates from, and an accountable human is named. Exit 0 = structurally valid, 1 = errors found (printed), 2 = malformed JSON. Use `--allow-class` when a rival genuinely belongs to an explanatory class outside the 8 standard ones — no script edit needed.

### 3. Derive discriminating predictions

For each candidate: state the observable, the expected pattern, a result that would falsify it, and which rival it's contrasted against — captured in the same JSON record's `predictions` array (validated by the same script above).

### 4. Lint the draft before sharing it

```bash
python scripts/lint_causal_claims.py draft.md [--fail-on high] [--include-quotes]
```

Flags overclaiming language with a suggested hedge, at three severities: **high** (clinical diagnosis/cure language, "no prior work exists"/"first study to"), **medium** ("proves," "confirms," "X causes Y," "definitively"), **low** ("due to," "leads to" — often legitimate). Every flag is printed; `--fail-on` only decides which severities make the run exit 1.

Hedged phrasing ("may cause," "could confirm") is not flagged. Fenced code blocks and blockquoted lines are skipped, since quoting someone else's overclaim to critique it is not the author overclaiming; `--include-quotes` scans them anyway. A line ending in `<!-- claim-ok -->` is skipped, for a claim the author has deliberately justified. This is pattern matching, not semantic understanding — review every flag, it will still miss paraphrased overclaims.

### 5. Generate a preregistration scaffold

```bash
python scripts/generate_preregistration_scaffold.py record.json -o preregistration.md
```

**Refuses to run unless the record passes step 2's validator, and there is no bypass flag.** This is the script that writes the document other people read, so a record with a "confirmed" candidate, no rival, or no accountable human must not be able to reach a preregistration through it — the validator is the gate, not a suggestion.

On success it fills sections 1-4 and 7 (question, observation, candidates, predictions, authorization) from the record; leaves the design/analysis-plan section (§5) as `<TODO>` for deliberate human/agent completion BEFORE touching outcome data, and a deviation log (§6) to fill only after that plan is timestamped. Exit 0 = written, 1 = record rejected (reasons printed), 2 = malformed input or existing output without `--force`.

### 6. Human accountability (always)

The accountable human verifies every citation, causal assumption, statistical design choice, and ethics/regulatory status — no script here substitutes for that review.

## Bundled files

- `scripts/validate_hypothesis_schema.py` — structural validator for a hypothesis record.
- `scripts/lint_causal_claims.py` — overclaiming-language pattern linter for any Markdown/text draft.
- `scripts/generate_preregistration_scaffold.py` — fills the preregistration template from a validated record.
- `assets/hypothesis_record_template.json` — the JSON schema template.
- `assets/preregistration_scaffold_template.md` — the preregistration document template.

## What this skill does NOT do

- Doesn't score, rank, select, or "pick a winner" among hypotheses — validation checks structure only.
- Doesn't search the literature itself — that's `literature-review`; establishing a dated evidence boundary is a separate manual/agent step this skill assumes has already happened.
- Doesn't call any LLM/AI API — pure stdlib pattern-matching and template-filling.
- Doesn't validate measurement operationalization, falsification controls, or evidence-ledger completeness — dropped from the original's 7-script suite for v0.1.0 (see above).
- Doesn't provide clinical diagnosis/treatment advice, dual-use technical detail, or bypass any required ethics/regulatory review.

## Known limitations (v0.2.0)

- The linter is still lexical. Severity levels and hedge-awareness cut the noise, but "due to" (low) fires on ordinary engineering prose, and a paraphrased overclaim ("the data leave no room for another explanation") matches nothing at all. It is a prompt to review, never an automatic rewrite, and a clean run is not evidence that a draft is well-hedged.
- The validator checks structure, never substance: two "rivals" that are the same explanation reworded, or a prediction that does not actually discriminate, both pass. Naming an accountable human is a declaration, not proof of review.
- No operationalization/measurement-validity checker, no falsification-controls checker, no evidence-ledger audit — a v2+ gap, not ported from the original in this round.
- The preregistration gate binds this skill's own generator. Nothing stops someone from hand-writing a preregistration around an invalid record — the gate reduces accidental misuse, it is not an access control.
