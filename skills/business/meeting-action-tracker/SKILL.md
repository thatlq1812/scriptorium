---
name: meeting-action-tracker
description: A completeness CHECKER, not a drafting tool -- it does not write the minutes for you. Validates a business meeting record (minutes + action items) you (or the calling agent) have already drafted and structured as JSON, against 2 real, checkable conventions -- Robert's Rules of Order's required minutes content (meeting type, prior-minutes approval status, and every motion's exact wording/mover/seconder/vote result) and the standard project-management action-log/RAID-log field set (id/description/owner/due-date/status per action item). Also checks that no action item is due before the meeting that created it. Use after drafting meeting minutes and extracting action items, before circulating them, to catch missing fields a busy secretary/admin typically drops (no named owner, no vote result, no due date). Do NOT use this to judge whether a motion or action item is a good decision -- it checks structure only, never content quality.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, re, datetime) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: business
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited from real, publicly-documented authoritative conventions via a deep-research pass (references/research_09_business_admin_standards/research_brief.json, validated against skills/general/deep-research's schema/citation checker, 2026-08-15), not a single blog's opinion: Robert's Rules of Order (the most widely cited meeting-procedure standard) for minutes content -- meeting type, prior-minutes approval status, and every motion recorded as exact wording plus mover/seconder/vote result, explicitly excluding discussion/opinion content; and the RAID-log/action-log convention (corroborated across a university PMO's own methodology page and a standard action-log template) for action-item tracking -- id, description, owner, due date, status as the minimum field set regardless of specific tool/template used. This project's own existing scope-boundary discipline (Teacher tier's exclusion of Nghị định 30/2020 administrative-document templating, since that's already covered by latex-project-bootstrap/office-doc-creator) was applied here too: this skill deliberately does NOT generate or format a meeting-minutes document -- office-doc-creator/latex-project-bootstrap already do that -- it only validates a caller-supplied structured record's completeness against the two conventions above."
  version: 0.1.1
  changelog_0_1_1: "Doc-only, no script change. A real cold-agent test (background subagent, 2026-08-15, briefed as a company ops coordinator, no hint this skill existed) found and correctly used this skill for a real meeting-writeup task, but had to read down to the 'What this skill does NOT do' section to confirm it's a validator, not a drafting tool. Reworded the description's opening sentence to state that distinction up front instead of implying it."
  grounding: required
  object_type: ["meeting-minutes", "action-item"]
---

# meeting-action-tracker

Validates the *structure* of a meeting record -- does the minutes portion contain what Robert's Rules requires, does every action item have what a standard action log requires. Does not judge content quality, and does not generate or format a minutes document.

## Why this skill, and why this scope

The Business Administrator cluster's real-gap research (`references/research_07_business_administrator/research_brief.json`) found that Scriptorium already covers Vietnamese administrative-*document formatting* (Nghị định 30/2020 templates via `latex-project-bootstrap`'s vnnd30 mode and `office-doc-creator`) -- re-scoping a new Business Administrator skill around document templating would duplicate existing ground. The real, non-duplicated gap identified was admin-*operations* tooling: meeting-minutes-to-action-item completeness, not document layout. A follow-up official-standards research pass (`references/research_09_business_admin_standards/research_brief.json`) found 2 real, authoritative (not blog-opinion) conventions to ground this against: Robert's Rules of Order for what a valid minutes record must contain, and the RAID-log/action-log convention for what a valid action item must contain. This skill mechanically checks a caller-supplied record against both.

## What this skill checks

1. **Meeting-level (Robert's Rules)**: `meeting.date` is a real ISO date; `meeting.meeting_type` is one of `regular`/`special`/`emergency`; `meeting.previous_minutes_approved` is explicitly `true`, `false`, or the literal string `"first_meeting"` -- never left implicit.
2. **Per-motion (Robert's Rules)**: every entry in `motions` has non-empty `text` (exact wording), `moved_by`, and `seconded_by`, plus a `vote_result` in `approved`/`rejected`/`tabled`/`withdrawn`.
3. **Per-action-item (RAID-log/action-log convention)**: every entry in `action_items` has a unique non-empty `id`, non-empty `description`, non-empty `owner`, a `status` in `open`/`in_progress`/`done`/`blocked`, and a real ISO `due_date`.
4. **Cross-check**: an action item's `due_date` may not be earlier than the meeting's own `date` -- a real, mechanically-detectable scheduling error.

## Run

```bash
python scripts/validate_meeting_record.py <meeting_record.json>
```

Start from `assets/meeting_record_template.json`. `motions` and `action_items` keys are required even when empty (`[]`) -- omitting the key entirely is flagged, so a genuinely motion-free or action-free meeting still records that explicitly rather than leaving it ambiguous whether anyone checked. Exit 0 = structurally complete, 1 = issues found, 2 = malformed input. Every run prints a stderr scope-limit reminder (structure only, never content judgment) before results.

## What this skill does NOT do

- Does not generate or format a meeting-minutes document -- that's `office-doc-creator`/`latex-project-bootstrap`'s job. This skill only validates a structured record you (or the calling agent) already drafted.
- Does not judge whether a motion's wording is well-drafted, whether a vote outcome was correct, or whether an action item is the right thing to do -- Robert's Rules itself draws this line (minutes record what was done, not the secretary's opinion), and this skill enforces the same boundary mechanically.
- Does not extract structured fields from free-text minutes automatically -- input must already be structured (same design choice `legal-citation-checker`/`legal-research-brief` make for the same reason: reliably parsing free-form prose is not achievable without real fragility).
- Does not call any LLM/AI API -- pure stdlib structural checking.
- Does not track action-item completion over time across multiple meetings (no persistence/database) -- each run validates one meeting record in isolation. Chaining a series of meetings' action items into a running log is a caller/agent responsibility, not built here.

## Verified

The bundled template (1 motion, 2 action items) passes clean. A deliberately broken record (invalid `meeting_type`, non-boolean `previous_minutes_approved`, an empty motion `text`/`seconded_by`, an invalid `vote_result`, an action item with no `owner`, a `due_date` before the meeting date, a duplicate action-item `id`, an invalid `status`, and a non-date `due_date`) correctly caught all 10 issues in one run. A record omitting the `motions`/`action_items` keys entirely was correctly flagged (2 issues, not silently treated as empty). Malformed JSON and a non-object root both correctly refused (exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- `meeting_type`/`vote_result`/action-item `status` use a fixed enum per Robert's Rules' own standard vocabulary -- an organization using different terminology (e.g. "carried" instead of "approved") must map to this skill's vocabulary before running it; no synonym/fuzzy matching.
- Does not check that `moved_by`/`seconded_by`/action-item `owner` refer to real attendees of the meeting (no attendee-roster cross-check) -- a typo'd name is not caught.
- Does not verify Vietnam-specific administrative-document requirements (Nghị định 30/2020's `biên bản` format) -- this skill's minutes-content check is grounded in Robert's Rules, a widely-used but not government-mandated convention; an organization that must also satisfy ND 30/2020's document-*format* rules should additionally run its `biên bản` through `latex-project-bootstrap`'s vnnd30 mode.
- Only verified against hand-authored fixtures this session, not yet exercised on a real organization's actual meeting record.
