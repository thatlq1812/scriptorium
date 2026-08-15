---
name: sop-structure-validator
description: A completeness CHECKER, not a drafting tool. Validates a Standard Operating Procedure (SOP) record you (or the calling agent) have already drafted and structured as JSON, against a real, widely-corroborated documentation convention -- a header (document id/version/effective date), purpose, scope, roles and responsibilities, sequentially-numbered steps, and a revision-history log with approval sign-off whose latest entry matches the document's current version. Use after drafting an SOP, before circulating or filing it, to catch missing sections a busy process-owner typically drops. Do NOT use this to judge whether the procedure itself is correct, safe, or well-designed -- it checks structure only, never content quality.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, datetime) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: business
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited from a real, publicly-documented authoritative convention via a deep-research pass (references/research_11_business_admin_sop_budget/research_brief.json, validated against skills/general/deep-research's schema/citation checker, 2026-08-15) -- a 6-part SOP structure (header/purpose/scope/roles/numbered-steps/revision-history-with-approval) corroborated across 3 independent English-language process-documentation sources, then confirmed structurally identical in Vietnamese-language SOP material (fastdo.vn) searched separately in the same round, per thatlq1812's direction to search Vietnamese sources too -- meaning this skill's grounding generalizes without needing a separate Vietnamese rule set. Deepens research_09's earlier, more generic ISO 9001 Clause 7.5 finding ('documented information must be controlled') into the specific, mechanically-checkable field set used here. Companion skill to meeting-action-tracker (same domain, same structural-validator-not-drafter shape) -- together they cover the 2 real Business Administrator gaps research_07 identified (admin-operations completeness checking) beyond the Nghị định 30/2020 document-*formatting* ground latex-project-bootstrap/office-doc-creator already cover."
  version: 0.1.0
  grounding: required
  object_type: ["sop", "process-document"]
---

# sop-structure-validator

Validates the *structure* of a Standard Operating Procedure record -- does it contain what a real, corroborated SOP-documentation convention requires. Does not judge whether the procedure itself is a good one, and does not generate or format an SOP document.

## Why this skill, and why this scope

`meeting-action-tracker`'s own research (`references/research_07_business_administrator/research_brief.json`) found Scriptorium's real, non-duplicated Business Administrator gap is admin-*operations* completeness checking, not document formatting (already covered by `latex-project-bootstrap`/`office-doc-creator`). A follow-up research pass (`references/research_11_business_admin_sop_budget/research_brief.json`) went past research_09's generic ISO 9001 finding ("documented information must be controlled") to find the specific, checkable structure real SOP-writing guides converge on. This skill mechanically checks a caller-supplied SOP record against that structure, same shape as `meeting-action-tracker`.

## What this skill checks

1. **Header**: non-empty `document_id`, non-empty `version`, a real ISO `effective_date`.
2. **Purpose and scope**: both non-empty text.
3. **Roles and responsibilities**: `roles_responsibilities` is a non-empty list; every entry has a non-empty `role` and `responsibility`.
4. **Procedural steps**: `steps` is a non-empty list, sequentially numbered starting at 1 with no gaps or duplicates; every entry has non-empty `text`.
5. **Revision history**: `revision_history` is a non-empty list; every entry has a non-empty `version`/`description`/`approved_by` and a real ISO `date`; the latest entry's `version` must match the document's top-level `version` (a real, mechanically-detectable staleness error -- the log wasn't updated when the document was).

## Run

```bash
python scripts/validate_sop.py <sop_record.json>
```

Start from `assets/sop_record_template.json`. `roles_responsibilities`, `steps`, and `revision_history` keys are required even if you'd otherwise be tempted to omit an empty one -- an SOP with zero named roles or zero steps isn't a valid SOP, so these are true requirements, not optional-with-`[]` like `meeting-action-tracker`'s motions/action-items (a meeting can genuinely have none; a valid SOP cannot have zero steps or zero responsible roles by definition). Exit 0 = structurally complete, 1 = issues found, 2 = malformed input.

## What this skill does NOT do

- Does not generate or format an SOP document -- that's `office-doc-creator`/`latex-project-bootstrap`'s job. This skill only validates a structured record you (or the calling agent) already drafted.
- Does not judge whether the procedure's steps are correct, safe, efficient, or achieve the stated purpose -- pure structural/field-presence checking, the same content/structure boundary `meeting-action-tracker` draws for minutes.
- Does not extract structured fields from a free-text SOP document automatically -- input must already be structured, same design choice as this project's other validators (reliably parsing free-form prose is not achievable without real fragility).
- Does not call any LLM/AI API -- pure stdlib structural checking.
- Does not verify ISO 9001 certification-audit readiness -- it checks a documentation *shape* widely associated with good SOP practice, not a formal ISO 9001 conformance audit (that requires a certified auditor, not a script).

## Verified

The bundled template (2 roles, 3 sequential steps, 1 revision-history entry matching the top-level version) passes clean. A deliberately broken record (empty `document_id`, an unparseable `effective_date`, empty `purpose`, an empty role name, a step-numbering gap (1, 3 instead of 1, 2), an empty step `text`, and a revision-history entry whose version doesn't match the document's current version) correctly caught all 7 issues in one run. A record with only the header fields (missing `roles_responsibilities`/`steps`/`revision_history` entirely) was correctly flagged (3 issues, not silently treated as valid). Malformed JSON and a non-object root both correctly refused (exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- Does not check that role names in `roles_responsibilities` match names/roles actually mentioned in the `steps` text -- no cross-reference between the two sections.
- Step-numbering validation requires exact sequential integers starting at 1 -- an SOP using a different numbering scheme (e.g. `1.1`, `1.2` sub-steps) must flatten to plain sequential integers first.
- Does not verify Vietnam-specific administrative-document requirements (Nghị định 30/2020's format rules) -- this skill's structure check is grounded in a general (English- and Vietnamese-corroborated) SOP-documentation convention, not a government-mandated format; an organization needing ND 30/2020 document-*format* compliance should additionally run the document through `latex-project-bootstrap`'s vnnd30 mode.
- Only verified against hand-authored fixtures this session, not yet exercised on a real organization's actual SOP.
