---
name: clinical-note-structure-validator
description: 'DOES NOT DIAGNOSE. DOES NOT REPLACE A LICENSED CLINICIAN. A STRUCTURAL-COMPLETENESS checker only -- never reads or judges clinical content. Checks that a client intake record declares completion, informed consent on file, and confidentiality-handling (per APA Ethics Code Standard 6.02/Human Relations), and that each SOAP-format session note (Subjective/Objective/Assessment/Plan) has every section present and non-empty. Use as an administrative completeness check before a note is filed -- never as clinical review, risk assessment, or diagnostic support. Do NOT use this to evaluate whether a session note''s content is clinically sound, whether a treatment plan is appropriate, or to suggest a diagnosis -- none of that is in scope, ever.'
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, datetime) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: psychology
  task_type: review-qa
  risk_tier: N4
  source: self-authored
  elicited_from: "Elicited from a deep-research pass (references/research_16_clinical_note_structure/research_brief.json, validated against skills/general/deep-research's schema/citation checker, 2026-08-15) -- the highest-risk grounding of any skill built this session, recorded honestly rather than softened. SOAP structure confirmed from a real, widely-deployed clinical-documentation product's own public documentation (SimplePractice), reverse-engineered per thatlq1812's explicit direction this session that this substitutes for real practitioner elicitation when none is available yet. Informed-consent/confidentiality requirements confirmed directly from the APA's own official Ethics Code (apa.org). The strict content/structure boundary this skill draws is independently corroborated by a real, already-scouted precedent in the same space (chengzhi43/ClarityGuide-skill), which explicitly states its own boundary as '不下诊断，不替代治疗师' (does not diagnose, does not replace a therapist) -- the same restraint applied here. risk_tier is N4 (not N2/N3 like this session's other skills) specifically because of the domain's real stakes; flagged for real practitioner review before any production use, not just documented as a known limitation."
  version: 0.1.0
  grounding: required
  object_type: ["clinical-note", "intake-record"]
---

# clinical-note-structure-validator

**DOES NOT DIAGNOSE. DOES NOT REPLACE A LICENSED CLINICIAN.** Checks only that a SOAP note's 4 sections are present and non-empty, and that intake/consent/confidentiality are declared. Never reads or judges clinical content.

## Read this before using this skill

This is the highest-risk skill Scriptorium has built to date (`risk_tier: N4`). Its grounding (`references/research_16_clinical_note_structure/research_brief.json`) is public-source and reverse-engineered-product material, NOT a real licensed clinician's input -- per thatlq1812's explicit direction this session that this substitution is acceptable when no real practitioner elicitation source exists yet, applied here at its most conservative. The resulting skill is scoped as narrowly as this project has ever scoped anything: it checks that required FIELDS EXIST and are NON-EMPTY, and does absolutely nothing else. It does not read what those fields say. It cannot and does not evaluate clinical judgment, suggest a diagnosis, assess risk, or judge a treatment plan's appropriateness. A real, independently-built precedent in this exact space (`chengzhi43/ClarityGuide-skill`) draws the identical line for itself -- this is not a Scriptorium-invented caution, it's a shared, necessary boundary anyone building in this space converges on.

## What this skill checks

1. **Intake record** (required whenever `session_notes` is non-empty): `completed` must be `true`; `informed_consent_on_file` must be `true` (APA Ethics Code); `confidentiality_handling_declared` must be `true` (APA Ethics Code Standard 6.02).
2. **Each session note**: a real ISO `session_date`; all 4 SOAP fields (`subjective`/`objective`/`assessment`/`plan`) present and non-empty. **The content of these fields is never read, parsed, or evaluated for meaning** -- only string presence/non-emptiness.

## Run

```bash
python scripts/validate_clinical_notes.py <record.json>
```

Start from `assets/clinical_note_template.json`. `session_notes` is required (use `[]` if there are none yet -- an empty list needs no `intake_record`). `intake_record` becomes required the moment `session_notes` is non-empty. Exit 0 = structurally complete, 1 = issues found, 2 = malformed input.

## What this skill does NOT do (read in full -- this is the point of the skill)

- **Does not diagnose.** Never suggests, infers, or comments on a diagnosis of any kind.
- **Does not evaluate clinical content.** The Assessment field's actual analysis, the Plan field's actual treatment plan, the Subjective field's actual reported experience -- none of it is read for meaning, only checked for non-emptiness.
- **Does not assess risk or safety.** Has no concept of crisis, risk level, or safety planning -- if any of that belongs in a note, a human clinician judges it, not this script.
- **Does not replace a licensed clinician, supervisor, or clinical-quality-review process.** This is an administrative completeness aid, comparable to a front-desk intake check, not clinical oversight.
- **Does not verify Vietnam-specific mental-health-practice regulation** -- this grounding is US-centric (APA, a US clinical-documentation product); a Vietnam-specific version needs separate, real research this session did not do.
- Does not call any LLM/AI API -- pure stdlib structural checking, the same as every other skill in this registry, but doubly important here: no model ever sees or reasons about the actual clinical content through this script.

## Verified

The bundled template (1 complete intake, 1 session note with all 4 SOAP fields present as placeholder text) passes clean. A deliberately broken record (`intake_record.completed: false`, `informed_consent_on_file: false`, an unparseable `session_date`, empty `subjective`, empty `assessment`) correctly caught all 5 issues in one run. A record with session notes but no `intake_record` key at all was correctly flagged. An empty `session_notes: []` list correctly passed without requiring an intake record. A record missing the `session_notes` key and malformed JSON both correctly refused/flagged (exit 2 / exit 1 respectively).

## Known limitations (v0.1.0, not yet through official quality-eval -- and should NOT be used in production without real practitioner review first)

- **This skill's grounding has not been reviewed by a real licensed psychologist or counselor.** It should not be treated as production-ready clinical-documentation tooling until that review happens -- this is flagged as a hard precondition, not a nice-to-have.
- No Vietnam-specific mental-health-practice regulation was researched -- US-centric grounding only.
- Does not check that `informed_consent_on_file`/`confidentiality_handling_declared` are backed by an actual real document -- takes the caller's declared boolean at face value, same as every other structural check in this registry, but the stakes of a false declaration here are categorically higher than in this session's other skills.
- Only verified against hand-authored, deliberately generic placeholder-text fixtures this session -- never exercised against any real clinical content, by design (real clinical content should never touch this skill's development/testing process without real practitioner oversight).
