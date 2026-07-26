---
name: legal-form-filler
description: A generic dossier-completeness checker and form-field-fill validator for legal/administrative procedures — the checklist and form template are always caller-supplied, never hard-coded, since this project has no real government procedure data. `check_dossier.py` checks a provided-documents list against a required-documents checklist (case/whitespace-normalized exact match); `fill_form.py` validates that every required form field has a value and flags data keys that don't match any declared field (catches typos); `checklist_from_catalog.py` mechanically extracts a checklist from a real Điều's Khoản list in a document-ai-structurer catalog.json, instead of the checklist being hand-typed with no source. Use when preparing a legal dossier or filling a form template. Do NOT use this to determine WHICH checklist/form applies to a given procedure — that selection judgment isn't automated here; the caller (or the agent, after reading the real Điều) supplies or picks the correct checklist/template.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-26) — check_dossier.py: a complete dossier passed with a correct informational note about an unmatched extra document, case/whitespace-normalized matching verified (lowercase "cmnd/cccd" matched the checklist's mixed-case entry), a missing-document case correctly flagged, malformed input refused (exit 2). fill_form.py: the bundled template (2 required + 1 optional field) filled correctly and rendered to Markdown; a missing required field correctly refused; a typo'd data key ("ngay_sin" instead of "ngay_sinh") was correctly flagged as both an unknown key AND left the real field "ngay_sinh" reported as unfilled — the exact real-world typo-catching case this design was built for. 2026-07-27: checklist_from_catalog.py verified end-to-end against a synthetic 2-document catalog — extracted a real Điều's 2-item Khoản list, fed it straight into check_dossier.py which correctly flagged 1 of 2 as missing; refusal paths (Điều with no Khoản, unknown số hiệu, unknown Điều number, malformed catalog) all correct.
metadata:
  domain: legal
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited from survey items 3, 4, 5 (outside_research/research_01_survey.md: form filling, form suggestion, dossier completeness checking). Item 4 ('Đề xuất biểu mẫu phù hợp' -- suggesting which form applies to a procedure) requires domain judgment about which of many possible Vietnamese administrative procedures a request maps to -- this project has no real checklist/template database for that judgment call, so it is explicitly OUT of scope here (not attempted, not guessed). Items 3 and 5 (filling a form, checking dossier completeness) are genuinely mechanical once a checklist/template is already known -- scoped down to a generic engine where BOTH the checklist and the form template are always caller-supplied input, never hard-coded, mirroring grade-book-builder's refusal to hardcode unverified official numbers. Full gap rationale: docs/ROADMAP.md §'Legal-cluster consolidation survey.' Owner (2026-07-27): directed wiring this skill into document-ai-structurer's catalog capability so a checklist can be grounded in a real cataloged Điều instead of always being hand-typed -- still does not decide WHICH Điều/document is the right one for a procedure, same domain-judgment gap as before, now just cheaper to extract once a human/agent has identified the right Điều."
  version: 0.2.0
  changelog_0_2_0: "Added checklist_from_catalog.py: given a document-ai-structurer catalog.json + văn bản số hiệu + Điều number, extracts that Điều's Khoản list verbatim as required_documents, in check_dossier.py's exact input schema. Mechanical extraction only -- does not judge whether the Khoản list is actually a document checklist (an Điều can enumerate obligations, deadlines, anything else); every run prints a reminder to verify this before trusting the output, same discipline as legal-citation-checker's --catalog scope-limit reminder."
  grounding: required
  object_type: ["dossier", "form"]
---

# legal-form-filler

Two generic engines: dossier-completeness checking and form-field-fill validation. The checklist and form template are always caller-supplied — this skill has no built-in knowledge of any specific Vietnamese administrative procedure.

## Why this skill, and why this scope

Survey items 3-5 asked for three things: filling a form, suggesting which form applies, and checking dossier completeness. The middle one — form *suggestion* — requires real domain judgment about which of many possible administrative procedures a request maps to, and this project has no real government checklist/template database to ground that judgment in. Rather than guess, it's explicitly out of scope, the same honesty already applied to `legal-citation-checker`'s hiệu-lực gap and `grade-book-builder`'s refusal to hardcode unverified TT22/2021 numbers. What's left — filling a *known* form and checking a dossier against a *known* checklist — is genuinely mechanical, so this skill is a generic engine where the checklist/template themselves are always input, never baked in.

## Run

### Dossier completeness

```bash
python scripts/check_dossier.py <checklist.json> <provided.json>
```

Start from `assets/checklist_template.json` and `assets/provided_documents_template.json`. Matching is case/whitespace-normalized exact string match — deliberately not fuzzy, since guessing whether two differently-worded document names refer to the same thing is exactly the kind of judgment call this skill avoids automating. Exit 0 = every required document present, 1 = at least one missing (each named), 2 = malformed input.

### Form filling

```bash
python scripts/fill_form.py <form_template.json> <form_data.json> [--render filled.md]
```

Start from `assets/form_template.json` and `assets/form_data_template.json`. Validates every field marked `required: true` has a non-empty value, and flags any data key that doesn't match a declared field name — a real, cheap way to catch a typo'd field name that would otherwise silently leave the intended field unfilled. Exit 0 = all required fields filled, 1 = at least one missing, 2 = malformed input.

### Checklist from a real structured document

Instead of hand-typing a checklist with no source, extract one from a real Điều's Khoản list in a `document-ai-structurer` catalog (`build_catalog.py` — see that skill's "Multi-document catalog" section):

```bash
python scripts/checklist_from_catalog.py <catalog.json> <van_ban_so_hieu> <dieu_number> -o checklist.json
```

This is mechanical extraction only — it does NOT judge whether that Điều's Khoản list is actually a document checklist (an Điều can enumerate obligations, deadlines, anything else, not just hồ sơ requirements). A human or the calling agent must already have read the real Điều text and confirmed it's a checklist provision before pointing this script at it; every run prints a reminder saying so. Exit 0 = extracted, 1 = Điều/document not found in the catalog or the Điều has no Khoản list, 2 = malformed input. The output plugs directly into `check_dossier.py` above.

## What this skill does NOT do

- Doesn't decide which checklist or form template applies to a given procedure — that domain judgment is explicitly out of scope (see "Why this skill" above); the caller supplies the correct one. **A real attempt was made (2026-07-27) to close this via `legal-web-search` against `dichvucong.gov.vn`** (the national public-service portal's procedure/form pages) — real WebFetch calls against 2 different page templates returned only a JS-rendered shell (no procedure/form content reachable), and a direct CSDL form-download link returned HTTP 503. The gap remains genuinely open, not solved by architecture alone; see `legal-web-search/SKILL.md`'s Known limitations for the reproduced findings before attempting this again with a different fetch method.
- Doesn't do fuzzy/semantic matching between document names — a document worded differently than the checklist entry, even if it's obviously the same thing to a human, is reported as missing rather than silently accepted.
- Doesn't render the final filled `.docx`/`.pdf` — delegate to `office-doc-creator` once a fill passes validation.
- Doesn't call any LLM/AI API — pure stdlib structural checking.

## Known limitations (v0.2.0)

- No fuzzy matching means a checklist/provided-documents list with inconsistent wording will produce false "missing" flags — this is a deliberate tradeoff (never guess a match) but does mean the checklist and provided-list wording need to be reasonably aligned by whoever prepares them.
- `fill_form.py` doesn't validate field VALUE format (e.g. that `ngay_sinh` is actually a valid date) — only presence/absence. A future version could add per-field type/format validation if real use shows the need.
- `checklist_from_catalog.py` extracts Khoản heading text verbatim, including any leading "1. "/"2. " numbering from the source document — not cleaned up into pure document-name strings. A checklist extracted this way may need light editing before it reads naturally, even though it's already correct for `check_dossier.py`'s matching purposes.
- Only verified against a small synthetic 2-document catalog this session — not yet exercised against a real Vietnamese legal document's actual hồ sơ-enumeration Điều.
