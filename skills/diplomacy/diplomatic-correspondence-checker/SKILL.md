---
name: diplomatic-correspondence-checker
description: A FORMAT/PROTOCOL checker, never a content or policy judge. Checks a note verbale's structural shape (third-person voice throughout, a recognizable opening compliments formula and closing valediction formula, non-empty sending/recipient office + reference number + date) against the real, stable diplomatic-correspondence convention, and checks a declared diplomatic-mission precedence list's ordering against the Vienna Convention on Diplomatic Relations (1961) -- ranked by precedence class, then by credential-presentation date within each class, never by the sending state's size/power/seniority. Use before a note verbale is sent, or before publishing/using a precedence-ordered list, to catch format mistakes. Do NOT use this to judge diplomatic or policy content -- it checks form only, and is not a substitute for a real protocol officer's judgment on any consequential matter.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, re, datetime) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: diplomacy
  task_type: review-qa
  risk_tier: N3
  source: self-authored
  elicited_from: "Elicited from a deep-research pass (references/research_14_diplomacy_protocol/research_brief.json, validated against skills/general/deep-research's schema/citation checker, 2026-08-15), reverse-engineered from real, authoritative public sources rather than a live practitioner survey, per thatlq1812's explicit direction this session that this substitution is acceptable when no real client elicitation source is available yet: the note-verbale structural convention is corroborated across 2 independent diplomatic-reference sources; the precedence-ordering rule is confirmed directly from a real official government protocol office (US Department of State), applying the Vienna Convention on Diplomatic Relations (1961), a stable, 60+-year-old international-law framework Vietnam is also party to. Deliberately scoped to FORMAT/PROTOCOL only, never diplomatic-content judgment, since public sources cannot and should not substitute for real diplomatic expertise on substance -- the same restraint this project already applies to legal-citation-checker's format-only scope and vn-ad-compliance-checker's route-don't-verify special-category handling."
  version: 0.1.0
  grounding: required
  object_type: ["diplomatic-correspondence", "precedence-list"]
---

# diplomatic-correspondence-checker

Checks note-verbale format and precedence-list ordering against real, stable diplomatic conventions. Never judges content, and is not a substitute for a real protocol officer.

## Why this skill, and why this scope

Scouting found zero real prior-art repos for International Relations (0 results in the earlier search round). thatlq1812 has real clients in this space, but per this project's own elicitation-tier discipline, IR content varies too widely across real use cases (embassy protocol vs. NGO policy analysis vs. trade negotiation) to ground generically -- that half of the cluster stays flagged, pending real client input. What IS buildable now, reverse-engineered from real official/authoritative sources per thatlq1812's explicit direction this session: the FORMAT layer of diplomatic work, which is genuinely stable and public (a note verbale's structure, and the Vienna Convention's precedence rule), the same kind of format-not-content restraint this project already applies to `legal-citation-checker`.

## What this skill checks

1. **Note verbale structure** (`note_verbale`, if given): non-empty `sending_office`/`recipient_office`/`reference_number`, a real ISO `date`, and a `body` that (a) contains a recognizable opening compliments formula, (b) contains a recognizable closing valediction formula, and (c) uses no first-person pronouns (I/we/our/us/my/me) anywhere.
2. **Precedence-list ordering** (`precedence_list`, if given): each entry declares a `precedence_class` (positive integer, 1 = highest), a `credential_presentation_date`, and a `declared_order`; the skill recomputes the correct order (by `precedence_class` ascending, then `credential_presentation_date` ascending within the same class) and flags if `declared_order` doesn't match.

## Run

```bash
python scripts/validate_diplomatic_correspondence.py <record.json>
```

Start from `assets/diplomatic_record_template.json`. Either `note_verbale` or `precedence_list` (or both) may be given -- at least one is required. Exit 0 = no flags, 1 = issues found, 2 = malformed input.

## What this skill does NOT do

- Does not and cannot judge diplomatic/policy content -- checks form only (third-person voice, opening/closing formula, precedence-ordering arithmetic), never what a note verbale actually says or whether a diplomatic position is sound.
- Does not verify a mission's precedence CLASS assignment itself (that's a real diplomatic-protocol determination) -- only that a caller-declared class+date ordering is internally consistent with the Vienna Convention's own rule.
- Does not generate a note verbale for you -- validates a drafted body you (or the calling agent) already wrote.
- Is not a substitute for a real protocol officer's judgment on any matter with real diplomatic consequence -- this is format-checking support, not a replacement for expertise.
- Does not call any LLM/AI API -- pure stdlib regex/structural checking.

## Verified

The bundled template (a well-formed note verbale + a correctly-ordered 3-mission precedence list) passes clean. A deliberately broken record (empty `sending_office`/`reference_number`, an unparseable `date`, a body missing both the opening and closing formula, first-person language ("I"/"we"), and a precedence list with 2 same-class missions declared out of credential-date order) correctly caught all 7 issues in one run. A record with neither `note_verbale` nor `precedence_list` and malformed JSON both correctly refused (exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- Opening/closing-formula detection is regex-based on common English phrasing ("presents its compliments," "avails itself... highest consideration") -- a note verbale using different but still-valid formal language, or written in a language other than English, would be incorrectly flagged. No non-English formula patterns are recognized yet.
- First-person detection is a simple word-boundary regex, not real grammatical parsing -- a body quoting another document verbatim (which might legitimately contain "I"/"we" inside a quotation) would still be flagged.
- Precedence-class assignment itself is entirely caller-declared and unverified -- this skill only checks internal consistency of a declared ordering, never the real-world correctness of the class assignment.
- Grounded via public/reverse-engineered sources, not real practitioner elicitation -- flagged explicitly in `elicited_from` and the research brief's own gaps section, not hidden. Treat this skill's output as a format-checking aid, not authoritative protocol guidance.
- Only verified against hand-authored fixtures this session, not yet exercised against a real embassy's actual correspondence or precedence list.
