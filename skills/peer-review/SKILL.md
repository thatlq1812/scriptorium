---
name: peer-review
description: Supports an accountable human reviewer in drafting a rigorous, actionable peer-review assessment — intake gate enforcing authorization/confidentiality/accountability, a claim-evidence alignment matrix, a private review scaffold with strict Comments-to-Authors/Confidential-Comments-to-Editor channel separation, and a tone/placeholder/decision-overreach linter. Use for authorized review of manuscripts, protocols, preprints, or proposals. Do NOT use without confirmed authorization from the publisher/editor/author — if authorization is unclear, this skill's intake validator blocks proceeding until it is resolved, by design.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, csv, re, argparse) — no dependency, no venv needed, local-only, zero network/model/external-service calls of any kind. Verified running clean on Claude Code (2026-07-26, v0.2.0); the run evidence is in `metadata.verified_runs`. No other harness verified — do not add one without testing it directly.
metadata:
  domain: general
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Grounded in K-Dense-AI/scientific-agent-skills peer-review (MIT, verified via gh api + per-folder license check 2026-07-26) for the mandatory safety boundary (confirmed authorization, confidentiality, never send unpublished content externally, never announce an editorial decision, human-accountability gate) and the intake-gate-first workflow pattern. Rewritten from scratch and scoped down from the original's 7-script/5-reference-doc suite to the 4 highest-value tools: intake validator, claim-evidence matrix validator, review-scaffold generator, and a tone/channel/placeholder linter -- dropped the reporting-guideline selector (needs a curated, kept-current guideline catalog, out of scope for v0.1.0), statistics/reproducibility audit checklist, and citation-key consistency checker as v2+ extensions."
  version: 0.2.0
  verified_runs: "2026-07-26, v0.2.0, Claude Code: a fully filled intake reached READY_FOR_LOCAL_REVIEW; the bundled template with only its 3 booleans flipped and every text field left as a placeholder was BLOCKED with 8 reasons and refused by the scaffold generator — the case that passed the gate in v0.1.0. The bundled claim-evidence matrix validated cleanly. The generated private scaffold was then linted and all 15 unfilled placeholders were caught, including multi-line ones, while its HTML comment block was correctly left alone. A draft using lowercase headings and the terms \"garbage collection\"/\"lazy evaluation\" produced zero false positives and still caught the real personal attack in it; a draft with \"Confidential:\" and a recommendation inside Comments to Authors was flagged as a channel leak; a clean draft passed with exit 0."
  changelog_0_2_0: "Fixed 4 defects found by re-testing v0.1.0, two of them in the gate this skill's safety rests on: (1) validate_review_intake.py accepted the bundled template's own placeholder strings as filled answers, so copying the template and flipping 3 booleans returned READY_FOR_LOCAL_REVIEW with no real authorization, no named human, and no retention plan; placeholders (`<...>`) now count as unfilled, ai_tool_policy is required (the doc demanded checking it, the tool ignored it) and 'not checked' is rejected, and conflicts_of_interest must be stated explicitly. (2) lint_review.py matched section headings by exact case-sensitive string, so a draft written as '## Comments to authors' was reported as missing channel separation entirely. (3) Its abusive-language check was substring-based: 'garbage collection' and 'lazy evaluation' were flagged as abuse while a real personal attack passed; the lexicon is now word-boundary matched, context-guarded, and paired with personal-attack patterns. (4) Placeholder detection only saw `<TODO>`, missing every multi-line instructional placeholder in the skill's own scaffold template. Added: channel-leak detection (editor-only content -- confidentiality notes, conflicts, integrity allegations, recommendations -- found inside Comments to Authors), decision-overreach narrowed to language that ANNOUNCES an outcome rather than recommends one, and overwrite/read-error guards on the generator."
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

Blocks on: undocumented authorization, unchecked venue policy, an unrecorded or unresolved AI-tool policy, declared external-service use, declared data reuse, missing retention/deletion plan, missing accountable human, undeclared conflicts of interest, or unresolved conflicts. Prints `READY_FOR_LOCAL_REVIEW` or `BLOCKED` with every reason — **proceed only when `READY_FOR_LOCAL_REVIEW`.**

A field still holding its template placeholder (`<...>`) counts as unfilled: copying the template and flipping the booleans does not pass this gate. This validates declarations, not their truth — it cannot know whether the named editor really assigned the review, only that someone was named.

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

Flags five rules: missing channel-separation headings (matched at any heading level, case-insensitively), unresolved placeholders (`<TODO>`, `[TODO]`, `TBD`, `{{...}}`, and multi-line `<...>` instruction blocks — HTML comments excluded), abusive language (word-boundary matched, so "garbage collection" and "lazy evaluation" are not flagged), personal attacks on the authors rather than the work, decision overreach, and **channel leakage** — editor-only content (confidentiality notes, conflict disclosures, integrity allegations, accept/reject recommendations) found inside `## Comments to Authors`.

Decision overreach means announcing an outcome ("this manuscript is rejected," "final decision:"), not recommending one — a reviewer recommending rejection to the editor is doing their job, so that phrasing is only flagged when it appears in the authors' channel. Exit 0 = clean, 1 = issues found (line numbers and rule IDs only; matched placeholders are truncated to 40 chars so the report never carries review text).

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

## Known limitations (v0.2.0)

- `lint_review.py`'s tone rules are hand-curated lexical patterns. They now avoid the obvious false positives and catch a few explicit personal-attack shapes, but most unprofessional tone is paraphrased and will pass — a safety net, not a tone-quality guarantee.
- The decision-overreach and channel-leak regexes catch common phrasings only. A differently worded overreach, or editor-only content phrased without any of the marker terms, will not be flagged.
- Channel-leak detection scans the `Comments to Authors` section for editor-only content. It does not attempt the reverse (ordinary scientific criticism misfiled in the editor channel) — judging what counts as "ordinary criticism" is not something a regex should decide.
- No automated "required actionability fields" enforcement beyond placeholder detection — the linter checks that placeholders are gone, not that a filled-in Location/Evidence/Action is actually well-formed.
- The intake gate validates declarations. It cannot verify that authorization is real, that the venue policy was actually read, or that a deletion plan will be honored — it makes those claims explicit and attributable, nothing more.
