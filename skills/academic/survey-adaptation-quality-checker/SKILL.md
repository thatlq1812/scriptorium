---
name: survey-adaptation-quality-checker
description: A PROCESS-DOCUMENTATION completeness checker, not a translation-quality judge. Validates a caller-declared record of how a survey/questionnaire instrument was translated and cross-culturally adapted, against the real, peer-reviewed TRAPD methodology (Translation by ≥2 translators with varied expertise, Review, Adjudication of disagreements, Pretest, Documentation) plus the back-translation cross-check convention. Use before deploying a translated/adapted survey instrument in social-science, psychology, management, or marketing research, to catch a skipped or undocumented quality-assurance step. Do NOT use this to judge whether the actual translation is linguistically accurate -- it checks that the required PROCESS was followed and documented, not the translation's real quality, which needs real bilingual subject-matter expertise this script does not have.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: academic
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited from a deep-research pass (references/research_15_survey_methodology/research_brief.json, validated against skills/general/deep-research's schema/citation checker, 2026-08-15) grounded in real, peer-reviewed survey-methodology literature -- the TRAPD approach and back-translation convention are each corroborated across 2+ independent peer-reviewed sources, and a formally Delphi-consensus-developed checklist (CTAQ) independently confirms the same quality-assurance shape. This is general-capability-tier public-source grounding (established academic research-methodology practice, not a specific researcher's tacit workflow), so it doesn't carry the same real-elicitation caution as the Diplomacy/Psychology candidates from the same session's cluster-completion round. A real, small (3-star) prior-art repo (gtskevin/survey-scale-review) confirmed genuine demand for this exact capability but wasn't large enough to harvest from -- this skill builds directly from the peer-reviewed literature instead. Extends Scriptorium's existing academic/research cluster (citation-management, literature-review) rather than starting a new specializer network."
  version: 0.1.0
  grounding: required
  object_type: ["survey-instrument", "questionnaire"]
---

# survey-adaptation-quality-checker

Checks a survey-translation-and-adaptation PROCESS record against the real, peer-reviewed TRAPD methodology. Never judges the actual translation's linguistic quality.

## Why this skill, and why this scope

Digital Marketing's earlier candidate-cluster review flagged Social Science's research-methodology half as buildable now (unlike the Psychology-clinical half, which needs real practitioner elicitation). Peer-reviewed survey-methodology literature (`references/research_15_survey_methodology/research_brief.json`) gives a real, stable, checkable process convention -- TRAPD (Translation/Review/Adjudication/Pretest/Documentation) -- for exactly the kind of thing this project already builds well: checking that a documented process was actually followed, not judging content requiring real expertise this project doesn't have (the same boundary `contract-risk-log`/`legal-research-brief` draw for their own domains).

## What this skill checks

1. **Translation**: `translators` must list at least 2 people, collectively covering at least 2 distinct expertise types (`survey_methodologist`/`translator`/`subject_matter_expert`) -- TRAPD requires varied expertise, not multiple people with the same single skill.
2. **Review and Adjudication**: `review_step_completed` must be `true`; `adjudication_notes` must document how translator disagreements were resolved.
3. **Back-translation**: `back_translation.performed` must be `true` with a named `back_translator_name` and `comparison_notes`, OR `false` with a stated `reason` for skipping it -- either is acceptable, but the key must be present and, if skipped, explained.
4. **Pretest**: `pretest.performed` must be `true` with a positive `sample_size` and documented `findings`, OR `false` with a stated `reason` -- same either-acceptable-but-explained shape as back-translation.

## Run

```bash
python scripts/validate_survey_adaptation.py <adaptation_record.json>
```

Start from `assets/adaptation_record_template.json`. `translators`, `back_translation`, and `pretest` keys are all required (the latter 2 may declare `performed: false` with a reason, but the key itself must be present -- omitting it is flagged, distinguishing "documented as skipped" from "never considered"). Exit 0 = process complete, 1 = issues found, 2 = malformed input.

## What this skill does NOT do

- Does not judge the actual translation's linguistic accuracy or cultural appropriateness -- that requires real bilingual subject-matter expertise this script does not have. It checks that the process steps happened and were documented, nothing about their substantive quality.
- Does not generate a translated instrument -- validates a process record for a translation/adaptation you (or the calling agent/research team) already performed.
- Does not check psychometric properties (reliability, validity, factor structure) of the adapted instrument -- scoped narrowly to the translation/adaptation-process convention only, not the broader field of scale validation.
- Does not call any LLM/AI API -- pure stdlib structural checking.

## Verified

The bundled template (2 translators with distinct expertise, a completed review/adjudication, a performed back-translation, and a performed pretest) passes clean. A deliberately broken record (only 1 translator, `review_step_completed: false`, empty `adjudication_notes`, `back_translation.performed: false` with no reason, `pretest.sample_size: 0`, and empty `pretest.findings`) correctly caught all 6 issues in one run. A record missing every key but `translators` (also missing) was correctly flagged (5 issues, no duplicate messages). Malformed JSON correctly refused (exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- `translators[].expertise` uses a fixed 3-value vocabulary (`survey_methodologist`/`translator`/`subject_matter_expert`) -- a research team using different role names must map to this vocabulary first.
- Does not check that `adjudication_notes`/`comparison_notes`/`findings` are substantively meaningful, only that they're non-empty text -- a caller could satisfy this check with a low-effort placeholder sentence; real review of the actual content remains a human/reviewer task.
- Does not verify translator credentials or independence (e.g. that the 2 translators actually worked separately before comparing) -- takes the caller's declared record at face value.
- Only verified against hand-authored fixtures this session, not yet exercised against a real research team's actual survey-adaptation process.
