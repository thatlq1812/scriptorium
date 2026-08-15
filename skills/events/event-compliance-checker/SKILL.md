---
name: event-compliance-checker
description: Checks a caller-declared Vietnamese public-event record against Nghị định 144/2020/NĐ-CP's real 2-pathway model -- the NOTIFICATION pathway (Điều 8 khoản 1/2 + Điều 9, internal/political/non-ticketed-venue performances, ≥5 working days advance notice, no approval wait) or the APPROVAL pathway (Điều 8 khoản 3 + Điều 10, the typical public/ticketed event, ≥7 working days advance submission, organizer-eligibility conditions, a real 5-working-day authority-response deadline, and a 2-working-day minimum notice for any time/location change to an already-approved event). Use before submitting an event-organizing application, or when auditing whether a planned event's timeline still satisfies the decree. Do NOT use this to verify the substance of security/fire-safety compliance, or as legal advice -- it checks declared facts against the decree's mechanical deadlines/eligibility rules only.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, datetime) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: events
  task_type: review-qa
  risk_tier: N3
  source: self-authored
  elicited_from: "Elicited from a deep-research pass (references/research_13_events_vn_compliance/research_brief.json, validated against skills/general/deep-research's schema/citation checker, 2026-08-15) grounded by directly reading Nghị định 144/2020/NĐ-CP's actual signed PDF page-by-page (Điều 1-10), the same primary-source discipline vn-ad-compliance-checker's grounding used for Nghị định 342/2025 -- not a secondary-source-only read. This caught and corrected a real discrepancy: a secondary source claimed a 10-working-day submission lead time; the primary decree text (Điều 10 khoản 4a) states 7 working days. Per thatlq1812's explicit direction this session on the 2 remaining candidate clusters (International Relations/Event Organization, Social Science/Psychology): where no real client elicitation source is available yet, reverse-engineering real official/authoritative sources is an acceptable substitute for the first flagship, same standing as this project's other general-capability-tier skills -- the Events half of the cluster was assessed as buildable this way (a well-documented public-permitting procedure), unlike the International Relations half proper (too varied/abstract across real use cases to ground generically without real client input, still flagged pending that source)."
  version: 0.1.0
  grounding: required
  object_type: ["event", "performance-permit"]
---

# event-compliance-checker

Checks a Vietnamese public-event record against Nghị định 144/2020/NĐ-CP's real, mechanically-checkable deadlines and eligibility rules. Does not verify compliance substance, and is not legal advice.

## Why this skill, and why this scope

Scouting for the new Events cluster found no comparable event-organizing skill-pack repo (unlike the Marketing cluster's 44k-star find) -- this skill builds from primary-source regulatory grounding instead, the same approach `vn-ad-compliance-checker` used for online advertising. Reading Nghị định 144/2020/NĐ-CP's actual text (not just secondary summaries) revealed a real 2-pathway structure invisible from blog-level sources: a lighter NOTIFICATION pathway for internal/non-ticketed cases, and a stricter APPROVAL pathway (with real eligibility conditions and a multi-step deadline cascade) for the typical public event.

## What this skill checks

1. **Pathway and lead time**: `event.pathway` must be `notification` or `approval`. Working days (Mon-Fri only, Vietnamese public holidays NOT accounted for) between `submission_date` and `planned_date` must be ≥5 for `notification` (Điều 9 khoản 4) or ≥7 for `approval` (Điều 10 khoản 4a).
2. **Approval-pathway eligibility** (only if `pathway: "approval"`): `organizer_entity_type` must be `public_institution`/`professional_association`/`registered_business` (Điều 10 khoản 1a); `security_order_compliance_declared` and `fire_safety_compliance_declared` must both be `true` (Điều 10 khoản 1b -- declared only, substance not verified).
3. **Authority response, if `approval_response` given**: once `application_complete_at_submission: true`, the `response_date` must be within 5 working days of submission (Điều 10 khoản 4c).
4. **Change notices, if `changes` given**: a content change requires a declared `content_change_notice_date`; a time/location change to an already-approved event requires at least 2 working days' notice before the new date (Điều 10 khoản 4đ).

## Run

```bash
python scripts/validate_event_compliance.py <event_record.json>
```

Start from `assets/event_record_template.json`. `approval_response` and `changes` are optional -- omit either if not yet applicable. Exit 0 = no flags, 1 = issues found, 2 = malformed input.

## What this skill does NOT do

- Does not verify the substance of security/fire-safety compliance -- Điều 10 khoản 1b references "quy định của pháp luật" generically without naming a specific fire-safety/security decree this project has separately verified; this skill only checks that compliance was declared, not that it's real.
- Does not constitute legal advice -- a flagged issue is a prompt for real review, not a final determination.
- Working-day counting excludes weekends only -- Vietnamese public holidays (Tết, ngày lễ) are NOT subtracted, a real, documented gap that can make a borderline-compliant timeline look compliant when it isn't.
- Does not cover competitions/festivals (Điều 11+) or any chapter beyond Điều 1-10 -- this skill's grounding only read that far; a future version should read further before extending scope.
- Does not call any LLM/AI API -- pure stdlib date-arithmetic and structural checking.

## Verified

The bundled template (approval pathway, 3-week lead time, a same-week authority response) passes clean. A deliberately broken record (a 2-working-day approval-pathway lead time, an ineligible `organizer_entity_type`, both compliance declarations false, a 10-working-day authority response, an invalid `response_type`, a missing content-change-notice date, and a 1-working-day time/location-change notice) correctly caught all 8 issues in one run. A notification-pathway record with only 1 working day's notice was correctly flagged alone. A record missing the `event` key and malformed JSON both correctly refused (exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- Vietnamese public holidays are not subtracted from working-day counts (see above) -- a real gap, not silently assumed away.
- Only Điều 1-10 of the decree were read for this skill's grounding -- Điều 10 khoản 4b's "incomplete application" 3-working-day request-for-completion deadline is not separately checked (only relevant once an authority has actually flagged an application incomplete, a state this schema doesn't yet model).
- Does not know which specific fire-safety/security decree governs the substantive compliance Điều 10 khoản 1b requires -- flags the declaration only, per this brief's own research gap.
- Only verified against hand-authored fixtures this session, not yet exercised against a real organizer's actual event-permitting timeline.
