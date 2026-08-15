---
name: translator-en-vi
description: Translates text English-Vietnamese and Vietnamese-English, keeping a natural register that matches the source tone (not forced into one fixed style) — detects formal/casual/technical register from the text itself, then maps it onto the target language. For legal/contract text specifically, a fixed EN-VI legal-term glossary plus a terminology-consistency checker keeps key terms (Indemnification, Force Majeure, Governing Law...) translated the same way every time — see "Legal terminology consistency" below. Use when translating documents, emails, technical descriptions, or any EN/VI text that needs to read naturally, as a native speaker would write it, not translated word-by-word. Do NOT use for legally binding text needing absolute terminology precision (contracts, statutes) that hasn't been reviewed by a qualified professional — this translation is for reference/communication only, not a substitute for a certified translation.
license: MIT
compatibility: 'Core translation is pure instructional, no script/dependency — uses the language capability of the consuming agent itself. check_terminology_consistency.py is stdlib-only (json, argparse), no dependency. Verified running clean: Claude Code (2026-07-26 core translation; 2026-07-27 terminology-consistency script — bundled template passes clean, an unregistered translation/an inconsistent-across-entries case/an unknown term_id typo/empty entries/malformed JSON all correctly caught).'
metadata:
  domain: general
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "thatlq1812 (2026-07-26): no fixed terminology glossary needed for general translation, a natural register that flexes with the source context rather than one forced style. The technical content (EN-VI contrastive notes on tense, classifiers, pronouns, idioms) was written from scratch based on public knowledge of contrastive linguistics. thatlq1812 (2026-07-27): directed completing the previously-planned legal-glossary extension (docs/ROADMAP.md, last item on the Legal-cluster shortlist) — a fixed EN-VI legal-term glossary + consistency check, same discipline legal-citation-checker's title-consistency and contract-consistency-linter's party-label checks already apply, now to terminology. Considered and declined renaming the skill to a bare 'translator' in the same session: registry/SCHEMA.md declares skill_id immutable, and the skill's actual capability (contrastive EN-VI linguistic notes) doesn't generalize to other language pairs without real work, so a bare name would misrepresent scope."
  version: 0.2.0
  changelog_0_2_0: "Added references/legal-glossary.json (10 starting EN-VI contract-term pairs, explicitly not an official standard, extensible) and scripts/check_terminology_consistency.py: validates a caller-supplied usage log against the glossary -- an unregistered translation, an unknown term_id (typo), and the same term translated 2 different ways across logged entries are all flagged. Doesn't scan free text for term occurrences itself (that judgment stays with the translator/agent) -- validates a usage record, same shape as this project's other consistency checkers."
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
- `references/legal-glossary.json` — fixed EN-VI legal/contract term pairs, see below.

## Legal terminology consistency

For general text, no fixed glossary — register/wording is decided contextually (see "What this skill does NOT do"). For **legal/contract text specifically**, key terms must be translated the same way every time, so `references/legal-glossary.json` fixes a starting set of EN-VI pairs (*Indemnification* → *Bồi hoàn*, *Force Majeure* → *Bất khả kháng*, *Governing Law* → *Luật áp dụng*, ...). This is explicitly a starting curated list, not an official government-published standard — no such free standard was found or supplied; extend the file directly when a real term/source is available.

After translating a legal document, log each glossary-term instance you used and validate it:

```bash
python skills/general/translator-en-vi/scripts/check_terminology_consistency.py usage_log.json
```

Start from `assets/usage_log_template.json`. This does NOT scan the translated text for term occurrences itself — you (the translator/agent) declare which glossary term you used where; the script only checks the declared usage is registered and consistent. Exit 0 = every logged term used its registered translation (or an approved alias) and the same term wasn't translated 2 different ways across entries; 1 = an issue found (unregistered translation, inconsistency across entries, or an unrecognized `term_id` — likely a typo); 2 = malformed input.

## What this skill does NOT do

- Doesn't create/use a fixed terminology glossary for GENERAL translation (thatlq1812 confirmed it isn't needed there) — decided contextually each time. The legal glossary above is a narrower, deliberate exception for contract/legal text specifically.
- Doesn't scan a translated document for glossary-term usage automatically — the usage log is caller/agent-declared, not auto-extracted.
- Doesn't substitute for a certified translation of legal text.
- Doesn't extend to a third language in v0.2.0 — add that when there's a concrete need, not built ahead of time.
