---
name: peer-review
description: Supports an accountable human reviewer in drafting a rigorous, actionable peer-review assessment — intake gate enforcing authorization/confidentiality/accountability, a claim-evidence alignment matrix, a private review scaffold with strict Comments-to-Authors/Confidential-Comments-to-Editor channel separation, and a tone/placeholder/decision-overreach linter. Use for authorized review of manuscripts, protocols, preprints, or proposals. Do NOT use without confirmed authorization from the publisher/editor/author — if authorization is unclear, this skill's intake validator blocks proceeding until it is resolved, by design.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, csv, re, argparse) — no dependency, no venv needed, local-only, zero network/model/external-service calls of any kind. Verified running clean: Claude Code (2026-07-26) — real valid intake correctly reached READY_FOR_LOCAL_REVIEW; a deliberately broken intake correctly triggered all 7 blocking conditions; the bundled claim-evidence matrix template validated cleanly (after fixing a real CSV-quoting bug found during this test — an unclosed quote merged two rows); a broken matrix correctly caught 5 errors; the scaffold generator correctly refused an unauthorized intake and generated correctly from an authorized one; the lint script passed a clean filled review and correctly flagged a missing channel-separation section, abusive language, and a decision-overreach phrase in a violating draft.
metadata:
  domain: general
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in K-Dense-AI/scientific-agent-skills peer-review (MIT, verified via gh api + per-folder license check 2026-07-26) for the mandatory safety boundary (confirmed authorization, confidentiality, never send unpublished content externally, never announce an editorial decision, human-accountability gate) and the intake-gate-first workflow pattern. Rewritten from scratch and scoped down from the original's 7-script/5-reference-doc suite to the 4 highest-value tools: intake validator, claim-evidence matrix validator, review-scaffold generator, and a tone/channel/placeholder linter -- dropped the reporting-guideline selector (needs a curated, kept-current guideline catalog, out of scope for v0.1.0), statistics/reproducibility audit checklist, and citation-key consistency checker as v2+ extensions."
  version: 0.1.0
  risk_tier_note: "N2, not N1: the tooling is fully local/deterministic, but the skill's subject matter (confidential manuscript review) carries real confidentiality/authorization risk if misused; the mandatory intake gate exists specifically to bound that risk."
---

# peer-review

Supports an accountable human reviewer with a rigorous, fair, actionable assessment. Every unpublished submission and review is confidential.

## Mandatory safety boundary — read before inspecting any manuscript

Before reading or analyzing unpublished content: confirm authorization by the publisher/editor/author, check the venue's confidentiality/AI-tool policy, record conflicts and competence limits, and default to local-only processing. If authorization is unclear, **do not inspect or quote the manuscript** — this skill's intake gate (step 1 below) enforces exactly this, blocking by design.

This skill and its scripts never: send unpublished content to an external service; upload confidential content anywhere; reuse content for training/benchmarking; read `.env`/credentials/environment secrets; call any network/LLM/image API; impersonate a reviewer/editor/journal/author; fabricate manuscript details, findings, or citations; or announce a decision that belongs to an editor/panel (a reviewer recommends, an editor decides — `lint_review.py` step 4 below flags exactly this kind of overreach).

## Why this differs from the original K-Dense-AI skill

The source skill's safety boundary, intake-gate-first workflow, and channel-separation discipline are excellent and entirely general-purpose — kept as-is. Its 7-script/5-reference-doc suite was scoped down to the 4 tools with the best value-to-complexity ratio for v0.1.0: intake validator, claim-evidence matrix validator, scaffold generator, and a lint script covering channel separation + placeholders + tone + decision-overreach in one pass. Dropped: the reporting-guideline selector (requires a curated, dated guideline catalog to stay accurate — a maintenance burden out of scope here), the statistics/reproducibility audit checklist, and the citation-key consistency checker — each a reasonable v2+ addition.

## Workflow

### 1. Intake gate (mandatory, blocks everything after it)

Copy `assets/review_intake_template.json`, fill it honestly, then:

```bash
python scripts/validate_review_intake.py completed-intake.json
```

Blocks on: undocumented authorization, unchecked venue policy, declared external-service use, declared data reuse, missing retention/deletion plan, missing accountable human, or unresolved conflicts. Prints `READY_FOR_LOCAL_REVIEW` or `BLOCKED` with every reason — **proceed only when `READY_FOR_LOCAL_REVIEW`.** This validates declarations, not their truth.

### 2. Map claims to evidence

Start from `assets/claim_evidence_matrix_template.csv` (one row per central claim: location, evidence IDs, alignment, limitation, requested action):

```bash
python scripts/validate_claim_evidence.py local-claim-matrix.csv
```

Reports IDs and counts only — never echoes the `claim_text`/`location` column content back, so the report itself is safe to share even though the underlying matrix file is confidential working material.

### 3. Review methods, statistics, reproducibility, ethics, figures/citations

Manual/agent review following the same priority order as the source skill (question/design → sampling/controls → sample-size rationale → missingness → analysis-design alignment → multiplicity → effect estimates → interpretation/generalizability), then reproducibility/transparency and ethics checks. Not automated in v0.1.0 — use `assets/claim_evidence_matrix_template.csv` findings plus direct expert judgment.

### 4. Draft the private scaffold, then lint before submitting

```bash
python scripts/generate_review_scaffold.py completed-intake.json -o private-review.md
```

Refuses to run unless the intake would pass step 1's validator. Fills the neutral header/summary; leaves `## Comments to Authors` (major/minor comments, each needing Location/Observation/Evidence/Why it matters/Requested action) and `## Confidential Comments to Editor` (conflicts, competence limits, specialist requests — NOT ordinary criticism) as separate sections to complete.

```bash
python scripts/lint_review.py private-review.md
```

Flags: missing channel-separation headings, unresolved `<TODO>`/placeholder text, a narrow abusive-language lexicon, and decision-overreach phrasing ("this manuscript is rejected" — a reviewer recommends, doesn't decide). Exit 0 = clean, 1 = issues found (with line numbers and rule IDs, never echoing the review text itself back).

### 5. Human accountability (always)

The accountable human reads the complete authorized submission, verifies every factual statement/citation/location, rewrites comments in their own judgment, and submits through the authorized channel. No script here establishes manuscript merit or substitutes for that read-through.

## Bundled files

- `scripts/validate_review_intake.py` — the mandatory authorization/confidentiality/accountability gate.
- `scripts/validate_claim_evidence.py` — claim-evidence matrix structural validator.
- `scripts/generate_review_scaffold.py` — private review-draft scaffold generator (gated on step 1 passing).
- `scripts/lint_review.py` — channel-separation, placeholder, tone, and decision-overreach linter.
- `assets/review_intake_template.json`, `assets/claim_evidence_matrix_template.csv`, `assets/review_scaffold_template.md`.

## What this skill does NOT do

- Doesn't select reporting guidelines (CONSORT/PRISMA/etc.) automatically — that catalog needs ongoing curation, out of scope for v0.1.0; consult the target venue's current guidance directly.
- Doesn't audit statistics/reproducibility or citation-key consistency automatically — dropped from the original's 7-script suite for this round; a v2+ gap.
- Doesn't call any LLM/AI API, network service, or external tool of any kind — pure stdlib validation/templating/linting.
- Doesn't decide accept/reject — no tool here produces or implies an editorial recommendation; that judgment stays entirely with the human reviewer.
- Doesn't verify that a claim is actually supported, that a citation exists, or that a reproduction was actually run — validators check structure/declarations, not truth.

## Known limitations (v0.1.0)

- `lint_review.py`'s abusive-language lexicon is narrow and hand-curated — it will miss most real instances of unprofessional tone; it is a safety net, not a tone-quality guarantee.
- The decision-overreach regex only catches a few common phrasings ("this manuscript is rejected," "editorial decision:") — a differently worded overreach will not be flagged.
- No automated "required actionability fields" enforcement beyond placeholder detection — the linter checks that `<TODO>` markers are gone, not that a filled-in Location/Evidence/Action is actually well-formed.
