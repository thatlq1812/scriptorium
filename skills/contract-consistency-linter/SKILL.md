---
name: contract-consistency-linter
description: Lints a Vietnamese contract text for three purely mechanical consistency errors — Điều (article) numbering (sequential, no gaps/duplicates), cross-reference integrity (every "Điều N" mention resolves to a real heading), and party-label consistency (only the declared parties, e.g. "Bên A"/"Bên B", appear — catches leftover copy-paste like a stray "Bên C" from a template). Use before finalizing or sending a contract. Do NOT use this to assess legal risk, clause fairness, or compliance — that's `contract-risk-log`'s job; this is a mechanical proofreading pass only, not a legal review.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (re, json, argparse) — no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-26). See "Verified" section below for the real test cases.'
metadata:
  domain: legal
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited from a real practitioner survey (outside_research/research_01_survey.md, item 7-8: a recent law graduate in a junior legal role, asked what work repeats and what a virtual assistant should do) -- items 7 ('Kiểm tra chính tả và định dạng... cách đánh số điều khoản') and 8 ('Kiểm tra tính nhất quán... tên các bên, số liệu, ngày tháng, định nghĩa, điều khoản tham chiếu và phụ lục') describe exactly the three checks this skill encodes. Scoped to only the subset of item 7-8 that is genuinely deterministic/mechanical (numbering, cross-references, party labels) -- date/defined-term consistency checking was judged too fragile to do reliably via regex for a v0.1.0 and is noted as a known limitation rather than attempted and shipped unreliable. First skill for the Legal specializer network (docs/specs/STRATEGY_SPEC.md §5.2), built after the education audience-tier ladder per owner's explicit sequencing this session, and chosen to build first within the legal cluster specifically because it required no external legal database and no owner-supplied checklist/template data -- unlike legal-citation-checker (no free Vietnamese legal-document API exists, unlike CrossRef for academic citations) or legal-form-filler (no real government checklist/template data available yet), both flagged as open gaps rather than built around with invented data."
  version: 0.1.0
  grounding: required
  object_type: ["contract"]
---

# contract-consistency-linter

Lints a Vietnamese contract for mechanical consistency: article numbering, cross-reference integrity, and party-label consistency. Pure proofreading — never assesses legal risk or clause quality.

## Why this skill, and why this scope

First skill for the Legal specializer network. Chosen to build first among the legal-cluster candidates specifically because it's the one with **no open data gap**: unlike `legal-citation-checker` (no free Vietnamese legal-document database/API exists to verify a statute's hiệu lực status, unlike CrossRef for academic citations) or `legal-form-filler` (no real government dossier checklist/template data available to this project yet), this skill only needs the contract text itself plus a short list of declared party labels — both supplied by the caller, nothing invented.

Elicited directly from a real junior-lawyer survey (`outside_research/research_01_survey.md`, items 7-8), which named exactly these three checks as high-frequency, error-prone, low-judgment work: "kiểm tra chính tả và định dạng... cách đánh số điều khoản" and "kiểm tra tính nhất quán... tên các bên... điều khoản tham chiếu." This skill covers the genuinely mechanical subset of those two items — date and defined-term consistency were judged too fragile for reliable regex-based checking in v0.1.0 and are left as a known limitation rather than shipped unreliable.

## What this skill checks

1. **Article (Điều) numbering** — every `Điều N` heading (a line starting with `Điều <number>`) must appear in strictly increasing order starting at 1, with no gaps and no duplicates.
2. **Cross-reference integrity** — every inline mention of `Điều N` in the body text (not a heading itself) must resolve to an `Điều N` heading that actually exists somewhere in the document. Catches the classic "referenced Điều 5 but the contract only has 4 articles" copy-paste error.
3. **Party-label consistency** — given a declared list of allowed party labels (e.g. `["Bên A", "Bên B"]`), flags any `Bên <X>` occurrence where `<X>` isn't one of the declared labels. Catches leftover template text (a stray "Bên C" from a different contract template that was never fully replaced).

## Run

```bash
python scripts/lint_contract.py <contract.txt> <config.json>
```

Start from `assets/lint_config_template.json` for the config shape (`allowed_party_labels`). The contract file is plain text/Markdown, UTF-8 — if the source is a `.docx`, extract its text first (e.g. via `document-ai-structurer`). Exit 0 = clean, 1 = issues found (each named with an exact line number), 2 = malformed input (missing file, invalid config).

## What this skill does NOT do

- Doesn't assess legal risk, clause fairness, or regulatory compliance — that's `contract-risk-log`'s job (a structured worksheet, not this mechanical lint).
- Doesn't check date consistency (e.g. an effective date mentioned in two places with different values) or defined-term consistency (a term defined once, referenced with a slightly different spelling elsewhere) — both judged too fragile for reliable regex detection in v0.1.0; a real gap, not silently ignored.
- Doesn't call any LLM/AI API — pure regex/stdlib mechanical checking.
- Doesn't verify statute citations inside the contract (e.g. "theo Nghị định 30/2020") resolve to a real, currently-effective legal document — that's the open gap flagged for `legal-citation-checker`.

## Verified

A real clean 3-article contract passed with zero flags; a deliberately broken contract (out-of-sequence numbering, a duplicate article number, 2 dangling cross-references, an undeclared "Bên C") was correctly flagged with all 5 issues named by exact line number; missing contract file, malformed config JSON, and a config missing the required field were all correctly refused with exit code 2.

## Known limitations (v0.1.0)

- Article-heading detection requires `Điều <number>` to start the line (after stripping leading whitespace) — a contract using a different heading convention (e.g. "ĐIỀU 1 —" in all caps, or a numbered-list format without the word "Điều") won't be recognized correctly. A future version could make the heading pattern configurable.
- Party-label detection is a simple `Bên <word>` regex — doesn't catch full company-name inconsistency (e.g. "CÔNG TY TNHH ABC" vs. "Công ty ABC" used interchangeably for the same entity) beyond the `Bên A`/`Bên B`-style shorthand.
- No date or defined-term consistency check (see "What this skill does NOT do" above) — flagged as a real gap for a future version, not attempted unreliably.
