---
name: pii-masking
description: Masks sensitive values (names, ID/CCCD/CMND numbers, phone numbers, emails, keyword-flagged account/tax numbers) in a text/markdown document before it enters an LLM context, and reverses the mask afterward. Two-step by design — scan_sensitive_patterns.py only proposes candidate structured identifiers for review, mask_terms.py mechanically masks an agent/human-approved term list (which must include any personal name or address, since those have no reliable regex and are not auto-detected), unmask.py reverses it using a LOCAL-ONLY mapping file. Use before sending any document containing real personal data (contracts, client files, student records) to an LLM call this skill doesn't control. Do NOT use as a substitute for reviewing the approved term list yourself — it masks exactly what it's told to, nothing more.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only, no dependencies. Verified running clean: Claude Code (2026-07-27, real round-trip test against a synthetic fixture with fake CCCD/phone/email/names).'
metadata:
  domain: general
  task_type: document-conversion
  risk_tier: N2
  source: self-authored
  elicited_from: "Owner (2026-07-27): explicit request for a 'mask sensitive info' skill for the Legal cluster. Grounded in 2 existing precedents already in this repo before generalizing: grading-and-feedback/anonymize_roster.py's local-only real-name<->code mapping (Quy chế AI Điều 6 discipline) and peer-review's confidentiality-gate pattern. docs/ROADMAP.md had already flagged this exact gap as 'a candidate for promotion to a shared foundation-tier utility if/when it's actually needed here, not built preemptively' — this is that promotion, generalized beyond the fixed roster-JSON schema to arbitrary free text, built as domain: general (not legal-specific) since the need is real across any skill handling personal data, matching document-ai-structurer's foundation-tier standing."
  version: 0.1.0
---

# pii-masking

Masks sensitive values in a text document by exact string replacement with stable placeholder codes (`[PII_01]`, `[PII_02]`, ...), and reverses it later using a local-only mapping file. Same shape as `document-ai-structurer`'s legal-article structuring mode: a candidate-scan step the tool proposes, a review step only the agent/human can do, and a mechanical apply step the tool executes exactly as approved — never all three collapsed into one blind pass.

## When to use

Use before any document containing real personal data (a contract, a client intake file, a legal brief, a roster) is sent into an LLM call this skill doesn't control — read the document back out already masked, work with it, then unmask only if and when the real values are needed again, locally.

Don't use as a name/PII *detector* on its own — `scan_sensitive_patterns.py` only catches structured, pattern-matchable identifiers (CCCD/CMND number shapes, VN phone numbers, emails, keyword-flagged digit runs). It does **not** detect personal names, home addresses, or free-text sensitive values — there is no reliable regex for a Vietnamese name. Those must be declared explicitly in `terms.json` by whoever prepares the document (the same discipline `grading-and-feedback/anonymize_roster.py` already uses for student rosters).

## Workflow

1. **Scan for structured candidates** (regex/keyword heuristics only, explicitly unverified output):
   ```bash
   python skills/pii-masking/scripts/scan_sensitive_patterns.py <input_file> -o findings.json
   ```
2. **Review `findings.json` yourself.** Every match's `context` field is included so you can judge — a bare 12-digit run is not always a CCCD number, a keyword-triggered digit run is not always the account number it looks like. Add any personal names/addresses you know are in the document; `scan_sensitive_patterns.py` will never find these on its own.
3. **Build `terms.json`** from the approved matches + any names/addresses you declared:
   ```json
   { "terms": ["Nguyễn Văn A", "0912345678", "012345678901"] }
   ```
4. **Mask** (mechanical — trusts `terms.json` completely, does no detection of its own):
   ```bash
   python skills/pii-masking/scripts/mask_terms.py <input_file> terms.json --out masked.md --map map.json
   ```
   Exit 0 means every declared term was found and masked at least once. Exit 1 means the masked file was still written, but at least one declared term had **zero** matches — check the report before assuming the document is safe to send anywhere; a term with zero matches was not actually masked (usually a typo, or a Unicode NFC/NFD normalization mismatch — the tool flags that specific case when it detects it). If a shorter term is a substring of an already-masked longer term in the same list (e.g. `"Văn A"` inside `"Nguyễn Văn A"`), it will correctly report zero matches too — it was already masked as part of the longer term, not missed.
5. **`map.json` is SENSITIVE and LOCAL-ONLY** — it contains the real value for every placeholder code. Never send its contents to any LLM/network call, same rule as `roster_map.json` in `grading-and-feedback`.
6. **Unmask when the real values are needed again**, still locally:
   ```bash
   python skills/pii-masking/scripts/unmask.py masked.md map.json --out unmasked.md
   ```

## Known limitations (v0.1.0, not yet through official quality-eval)

- No personal-name or address detection — by design, not an oversight (no reliable regex exists; a false negative here is a real PII leak, so guessing was deliberately ruled out in favor of requiring an explicit declared list).
- Date-of-birth detection is weak: a slashed format like `01/01/1990` doesn't match the keyword-triggered digit-run pattern (which requires one contiguous run of 6-19 digits) — flagged, not silently claimed as covered.
- `mask_terms.py`/`unmask.py` do exact string matching only — a term with inconsistent spacing, capitalization, or Unicode normalization from its occurrence in the document will be reported as zero matches (loudly, via exit code 1) rather than silently missed, but won't be masked either; fix the term and re-run.
- Verified only against a synthetic fixture this session (`assets/sample_document.md`, hand-authored fake data — no real client/legal document was available or needed to build this, per owner direction). Real-world documents with messier formatting (OCR noise from `document-ai-structurer`, inconsistent spacing) not yet tested.
- Not yet wired into any Legal-cluster skill's workflow (`contract-risk-log`, `legal-research-brief`, `contract-consistency-linter`) — those skills don't call this one automatically; masking is currently a manual step the calling agent chooses to run.
- Hasn't passed stage 4 (quality eval, ≥2 harnesses) or stage 5 (security audit — self-audited only this session: stdlib-only, no eval/exec/subprocess/os.system/network calls found in any of the 3 scripts).
