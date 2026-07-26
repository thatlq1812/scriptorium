---
name: translator-en-vi
description: Translates text English-Vietnamese and Vietnamese-English, keeping a natural register that matches the source tone (not forced into one fixed style) — detects formal/casual/technical register from the text itself, then maps it onto the target language. Use when translating documents, emails, technical descriptions, or any EN/VI text that needs to read naturally, as a native speaker would write it, not translated word-by-word. Do NOT use for legally binding text needing absolute terminology precision (contracts, statutes) that hasn't been reviewed by a qualified professional — this translation is for reference/communication only, not a substitute for a certified translation.
license: MIT
compatibility: Pure instructional, no script/dependency — uses the language capability of the consuming agent itself. Verified running clean: Claude Code (2026-07-26).
metadata:
  domain: general
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Owner (2026-07-26): no fixed terminology glossary needed, a natural register that flexes with the source context rather than one forced style. The technical content (EN-VI contrastive notes on tense, classifiers, pronouns, idioms) was written from scratch based on public knowledge of contrastive linguistics."
  version: 0.1.0
---

# translator-en-vi

Translates EN↔VI to read naturally, as a native speaker would write it, not word-for-word. Initial scope is EN-VI/VI-EN only (extend to other languages later if needed — no concrete need yet).

## Process

1. **Read the source text, detect its register** — formal/casual/technical (see `references/register-detection.md` for the concrete signals to look for). Don't default to one fixed register for every translation.
2. **Translate for meaning and communicative function, not word-by-word** — pay particular attention to the EN↔VI structural differences listed in `references/common-pitfalls-en-vi.md` (verb tense, classifiers, personal pronouns, idioms, technical loanwords).
3. **Mandatory self-check**: read the translation back independently, without looking at the source side by side — if you need to go back to the source to understand the translation, it isn't good enough yet, fix it.
4. **High risk (risk_tier N2)**: if the text carries legal/contractual weight, always tell the user clearly that this translation is for reference only, not a substitute for a certified/legally-qualified translation.

## Bundled files

- `references/register-detection.md` — signals for detecting the source's register + how to map it onto the target language.
- `references/common-pitfalls-en-vi.md` — 5 common error types specific to the EN↔VI pair, with how to handle them.

## What this skill does NOT do

- Doesn't create/use a fixed terminology glossary (owner confirmed it isn't needed) — decided contextually each time.
- Doesn't substitute for a certified translation of legal text.
- Doesn't extend to a third language in v0.1.0 — add that when there's a concrete need, not built ahead of time.
