---
name: parent-school-communicator
description: Checks a parent/guardian's message TO a school or teacher (meeting request, concern, follow-up, inquiry, absence notice, complaint) for structural completeness and tone before it's sent -- required fields present (who it's addressed to, who the child is, what's being asked), no leftover template placeholder, a concrete requested action always present (this direction of communication has no valid pure-FYI case), and no hostile/threatening escalation language toward the teacher/school. Use when a parent or an agent acting on a parent's behalf has drafted a message to a school and wants it checked before sending. Do NOT use this to generate the message content itself (no LLM/AI call -- it only checks a filled-in record), to judge writing quality/persuasiveness, or to draft a teacher-to-parent message (that is the opposite direction, covered by parent-communication).
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, re, argparse) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Public-source grounding, general-capability tier per CLAUDE.md principle 4 (no expert interview needed -- this is not a niche-specializer skill). The required-content shape (who this is addressed to, who the child is, what actually happened, what the parent wants done, how to reach back) is the well-documented convention for a professional parent-to-school communication found across public school-communication guidance (e.g. PTA/parent-advocacy 'how to write to your child's teacher' guides, school-district 'contacting your child's teacher' pages) and mirrors the same required-content shape this project already validated and shipped in the opposite direction in skills/education/parent-communication/SKILL.md (a real previously-deployed prior system skill, teacher-to-parent). Explicit boundary check performed against parent-communication before building this (see 'Why this skill, and why this scope' below): parent-communication validates a message flowing teacher->parent (school-authored, and its one hard-block is an unfilled STUDENT NAME on a single-student letter, with requested_action allowed to be empty for a pure-FYI message); this skill validates the opposite flow, parent->school (parent-authored, its equivalent hard-block is an unfilled RECIPIENT contact, and requested_action is never allowed to be empty because a parent initiating contact with a school is assumed to always want a concrete next step). The two skills share only the generic placeholder-detection regex and the two-tier errors/warnings validation shape already established by parent-communication -- the required-field set, the hard-block condition, and the tone lexicon (hostility toward the school/teacher, not harshness about the student) are each direction-specific and were re-derived, not copy-pasted assuming equivalence."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["letter", "email"]
---

# parent-school-communicator

Checks a parent/guardian's message to a school or teacher -- a meeting request, a concern, a follow-up, an inquiry, an absence notice, or a complaint -- for completeness and tone before it's sent. Catches the boring, embarrassing failure modes deterministically: a missing required field, a leftover template placeholder, an unstated concrete ask, or hostile/threatening language that would derail the message before it's even read.

## Why this skill, and why this scope

This is the Parent/Guardian-tier counterpart to `parent-communication`, but running the opposite direction: `parent-communication` checks a homeroom teacher's letter/brief TO parents (school-authored); this skill checks a parent's message TO the school (parent-authored). Both validate "does this piece of home<->school correspondence have what it needs before it goes out," but the two directions genuinely differ in what "complete" means:

| | `parent-communication` (teacher -> parent) | `parent-school-communicator` (parent -> school, this skill) |
| --- | --- | --- |
| Required-field-that's-a-hard-block | Unfilled `student_name_or_placeholder` on a single-student letter | Unfilled `recipient_name` (the teacher/school contact never actually named) |
| `requested_action` | Optional -- a pure-FYI brief with no ask is valid | Always required and non-empty -- a parent initiating contact with a school is assumed to always want a concrete next step, even if it's just "please confirm receipt" |
| Tone lexicon | Harsh/accusatory language *about the student* (a teacher judging a child's character) | Hostile/threatening escalation *toward the teacher/school* (a parent's grievance tipping into a threat rather than a firm, constructive ask) |
| Recipient scope | `single_student` vs `whole_class` (a teacher addressing one family or the whole roster) | Always one student, one named school contact -- no whole-class analog exists on this side |

This boundary was checked explicitly before building this skill (not assumed) -- the two do not overlap ≥80% despite superficial similarity ("a validator for a home<->school message"): the required-field set, the one hard-blocking condition, and the tone lexicon are each direction-specific, not mirror-images of the same data. Building this as a separate skill rather than extending `parent-communication` keeps each skill's domain knowledge (what "complete" means for its specific direction) legible on its own, the same way `legal-form-filler` and `contract-consistency-linter` stay separate skills despite both operating on legal documents.

## What domain knowledge this validator encodes

- **A parent-initiated school message always names who it's for and who it's about.** `recipient_name`/`recipient_role` (the teacher or school staff being addressed) and `student_name` (the child the message concerns) are both required non-empty fields -- unlike `parent-communication`, there is no "whole class" analog here; a parent is always writing about their own child to a specific school contact.
- **The concrete ask is never optional in this direction.** `parent-communication` explicitly allows an empty `requested_action` for a pure-FYI periodic brief (a teacher informing, not asking). A parent contacting a school is the opposite case -- even an "FYI" absence notice implicitly asks the school to excuse/record the absence. This validator therefore hard-requires a non-empty, non-placeholder `requested_action` for every `communication_type`, with no FYI exception.
- **The equivalent hard-block, mirrored from `parent-communication`'s single-student-name check**: a message with `recipient_name` left as an unfilled template placeholder is the parent-side version of the same embarrassing mistake `parent-communication` catches (a form letter sent with the placeholder never replaced) -- here it's a message that was never actually addressed to a real person before being sent.
- **Tone constraint, re-derived for this direction, not inverted from `parent-communication`'s lexicon.** A parent raising a concern or complaint has every right to be firm; the failure mode this validator targets is a message that tips into hostility or a conditional threat toward the teacher/school (e.g. "if this isn't fixed I will sue" / "toi se bao cong an") rather than a legitimate, constructive concern. Flagged as a warning, not a hard error, for the same reason `parent-communication`'s tone lexicon is a warning: tone judgment is inherently soft, and a firm-but-fair message should not be blocked.

## How to run

```bash
python scripts/validate_school_message.py <message.json>
```

Start from `assets/school_message_template.json`. It has 9 fields:

| Field | Meaning |
| --- | --- |
| `communication_type` | One of `meeting_request`, `concern`, `follow_up`, `inquiry`, `absence_notice`, `complaint`. |
| `recipient_name` | Full name of the teacher/school staff this is addressed to -- REQUIRED, cannot be a placeholder. |
| `recipient_role` | e.g. "Giao vien chu nhiem", "Hieu truong", front-office admin. |
| `sender_name` | Parent/guardian full name. |
| `student_name` | The child's full name -- always required, this direction is always about a specific student. |
| `purpose` | Free text: what this communication is for. |
| `body_sections` | List of the actual content points (at least 1 non-empty item required). |
| `requested_action` | The concrete ask -- REQUIRED and non-empty, never a valid pure-FYI empty value in this direction. |
| `contact_info` | How the school can reply -- leave empty rather than inventing one. |

Exit 0 = passes (warnings, if any, print above the VALID line -- they're tone signals worth reading, not blocking). Exit 1 = at least one error (missing/empty required field, unresolved placeholder anywhere in the record, an empty/placeholder `requested_action`, or -- the hard-blocked case -- an unfilled/placeholder `recipient_name`). Exit 2 = file not readable or malformed JSON.

## What this skill does NOT do

- **Does not generate the message content.** No LLM/AI call, ever (per this project's standing rule -- Scriptorium skills never integrate an AI backend). A human or an agent writes `purpose`/`body_sections`/`requested_action` first; this only checks the filled-in record before it goes out.
- **Does not judge writing quality, persuasiveness, or whether the content is actually true/fair** -- it checks completeness and a narrow, mechanical tone lexicon, nothing else. A message can pass this validator and still be a bad message.
- **Does not render a `.docx`/email.** Delegate that to `office-doc-creator` once the JSON record passes validation -- same division of labor as `parent-communication`.
- **Does not validate a teacher-to-parent message.** That is `parent-communication`'s scope -- opposite direction, different required-field set and hard-block, do not use this skill for that case (see "Why this skill" table above).
- **Does not decide whether a complaint is legally/administratively warranted**, does not route to a formal grievance process, and does not check the message against any specific school's actual complaint-handling policy -- purely a completeness/tone check on the message record itself.

## Verified

A complete meeting-request message (single student, named recipient, concrete requested date/action) validated with zero errors/warnings. A message with an unfilled `<recipient_name>` placeholder correctly refused (exit 1, naming the placeholder). A concern message with an empty `requested_action` (a parent trying to send a pure-FYI-style concern with no ask) correctly refused (exit 1, naming `requested_action`) -- this is the direction-specific hard-require this validator adds that `parent-communication` deliberately does not have. A complaint message containing an escalating conditional-threat phrase ("neu khong xu ly toi se bao cong an") correctly warned (exit 0, 1 warning) without blocking. A message missing `student_name`/`sender_name` correctly refused (exit 1, 2 errors). A `requested_action` left as `<TODO>` correctly refused. Malformed JSON and an empty `body_sections` list both correctly refused (exit 2 and exit 1 respectively). An absence-notice message with a concrete, non-placeholder `requested_action` ("xin phep cho con nghi hoc ngay 15/9 vi ly do suc khoe") correctly passed with zero warnings.

## Known limitations (v0.1.0)

- The hostile/threat lexicon (`HOSTILE_RE`/`THREAT_RE` in the script) is small and hand-curated, mostly Vietnamese with a few English terms. It will miss paraphrased hostility and will not catch every real tone problem -- read it as a tripwire for the most common escalation phrasings, not a complete tone judge. A firm, entirely reasonable complaint can still legitimately trigger a warning if it happens to contain a flagged phrase (e.g. "toi se bao cho ban giam hieu" is not flagged, but "toi se to cao" is) -- warnings are not proof of bad faith, they're a prompt to re-read before sending.
- Placeholder detection reuses `parent-communication`'s exact pattern (`<TODO>`, `[TODO]`, `{{...}}`, `TBD`, `XXX`, bare `<...>` tokens) verbatim. A placeholder written in an unrecognized style (e.g. `___FILL_IN___`) will not be caught.
- No cross-check that `requested_action` content is actually consistent with `communication_type` (e.g. a `meeting_request` with no time/place mentioned anywhere in `body_sections`) -- this validator only checks that *something* concrete was requested, not that the right thing was requested for this message type, same documented limitation as `parent-communication`.
- No support for a message concerning more than one child (e.g. a parent with two children at the same school raising one combined concern) -- `student_name` is a single required string; a multi-child message would need to be split into separate records or a future version would need a `student_names` list.
