---
name: hypothesis-generation
description: Turns an observation into a transparent set of rival candidate hypotheses, discriminating predictions, and a preregistration-ready plan — never presenting any hypothesis as established fact. Use when moving from an observation/preliminary finding to a testable research plan, or when a draft is at risk of overclaiming causation/certainty. Do NOT use for patient-specific diagnosis, treatment, or clinical advice — this skill is a structured-thinking + drafting aid, not a scoring or decision system, and the accountable human always verifies the output.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, re, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-26) — real hypothesis record (3 rival candidates: mechanism/selection-bias/confounding, 2 discriminating predictions) validated successfully; a deliberately broken record (status="confirmed", <2 candidates, dangling prediction reference, missing accountable_human) correctly caught all 4 errors; causal-claim linter correctly flagged 5 overclaiming patterns in a drafted paragraph and passed a hedged rewrite of the same paragraph clean; preregistration scaffold correctly generated from the valid record.
metadata:
  domain: general
  task_type: research
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in K-Dense-AI/scientific-agent-skills hypothesis-generation (MIT, verified via gh api + per-folder license check 2026-07-26) for the object model (observation/hypothesis/prediction/estimand kept distinct), non-negotiable boundaries (never present a hypothesis as fact, no clinical claims, human-accountability gate, no auto-scoring), and the general workflow (freeze observation -> generate rivals -> derive discriminating predictions -> preregister). Rewritten from scratch and scoped down from the original's 7-script/9-reference-doc suite to the 3 highest-value, most general-purpose tools: a JSON schema validator enforcing the rivals+status-never-confirmed rules, a causal-claim language linter, and a preregistration-scaffold generator -- dropped format-specific validators (operationalization checklist, falsification/controls, evidence-ledger audit) as a v2+ extension if the need materializes."
  version: 0.1.0
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
python scripts/validate_hypothesis_schema.py record.json
```

Checks structural completeness: every candidate stays labeled `"status": "candidate"` (never `confirmed`/`proven`/`established`), at least 2 rivals exist, every prediction references a real candidate and at least one rival it discriminates from, and an accountable human is named. Exit 0 = structurally valid, 1 = errors found (printed), 2 = malformed JSON.

### 3. Derive discriminating predictions

For each candidate: state the observable, the expected pattern, a result that would falsify it, and which rival it's contrasted against — captured in the same JSON record's `predictions` array (validated by the same script above).

### 4. Lint the draft before sharing it

```bash
python scripts/lint_causal_claims.py draft.md
```

Flags overclaiming language ("proves," "confirms," "X causes Y," "no prior work exists," clinical diagnosis/cure language) with a suggested hedge. This is pattern matching, not semantic understanding — review every flag, it will miss paraphrased overclaims and can flag legitimate quoted text.

### 5. Generate a preregistration scaffold

```bash
python scripts/generate_preregistration_scaffold.py record.json -o preregistration.md
```

Fills sections 1-4 and 7 (question, observation, candidates, predictions, authorization) from the validated JSON record; leaves the design/analysis-plan section (§5) as `<TODO>` for deliberate human/agent completion BEFORE touching outcome data, and a deviation log (§6) to fill only after that plan is timestamped.

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

## Known limitations (v0.1.0)

- `lint_causal_claims.py`'s `\b\w+ causes? \w+` pattern is broad and will over-flag benign phrasing ("this causes a small delay in the pipeline") alongside genuine overclaims — treat every flag as a prompt to review, not an automatic rewrite.
- No operationalization/measurement-validity checker, no falsification-controls checker, no evidence-ledger audit — a v2+ gap, not ported from the original in this round.
- `validate_hypothesis_schema.py`'s candidate-class enum is fixed to the 8 classes in the original skill; a genuinely novel rival class not on that list will be rejected structurally even if scientifically valid — extend `CANDIDATE_CLASSES` in the script if this becomes a real blocker.
