---
name: parent-communication
description: Checks a homeroom teacher's message to parents (a one-off letter/notice or a periodic weekly/monthly brief) for completeness and tone before it goes out — required fields present, no leftover template placeholder (especially an unfilled student name on a single-student letter), a concrete requested action if one is stated, and no harsh/accusatory language about the student. Use when a teacher or agent has drafted a parent letter or periodic brief and wants it checked before sending. Do NOT use this to generate the message content itself (no LLM/AI call — it only checks a filled-in record), to judge writing quality/persuasiveness, or for school-administration paperwork (reports, decisions, correspondence logs — out of scope for this tier).
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, re, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-26). See "Verified" section below for real test-case detail.
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Consolidates 2 prior system skill folders that are the same underlying task at different cadence: prior deployed system skills/parent_letter/SKILL.md (a one-off letter/notice — meeting invitation, result notification, cooperation request, reminder) and prior deployed system skills/parent_brief/SKILL.md (a periodic weekly/monthly per-student or whole-class brief, explicitly framed as replacing ad-hoc Zalo messages). Both are real previously-deployed prior system skills for Vietnamese K12 homeroom teachers. Per owner direction (2026-07-26 consolidation pass), the ~63-folder prior system skill set is being consolidated into fewer, more practical skills; parent_letter and parent_brief were judged in-scope for this tier (unlike prior system's bureaucratic-paperwork skills, which the owner explicitly excluded) because parent communication is core homeroom-teacher work, not school-administration process. Domain knowledge kept: the required-content shape both skills converge on (purpose, addressed content, a clear ask if any, sender identity, contact info) and their shared tone constraints (respectful/clear, no exaggeration, no comparative-ranking or other-student PII, no harsh judgment of the student, do not fabricate specific student facts). prior system's own orchestration machinery in both SKILL.md files (persona/effort/token_budget tuning, planning-gate question sequencing, Jinja2 `{{ user.* }}`/`{{ institution.* }}` profile placeholders, workspace-scan-before-work, `llm_call`/`script_exec`/`request_input` tool orchestration, the DOCX-building pipeline itself) was NOT ported — this skill never calls an LLM/AI API and is a single deterministic completeness+tone validator over a JSON record a human or agent has already filled in, not a content-generation SOP."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["letter", "parent-brief"]
---

# parent-communication

Checks a homeroom teacher's message to parents — a one-off letter/notice or a periodic (weekly/monthly) brief — for completeness and tone before it's sent. Catches the boring, embarrassing failure modes deterministically: a missing required field, a leftover template placeholder, a vague call-to-action, or harsh language about the student that slipped into a draft.

## Why this skill, and why this scope

Consolidates 2 prior system skill folders that are the same underlying task at different cadence: `parent_letter` (a one-off letter — meeting invite, result notice, cooperation request, reminder) and `parent_brief` (a periodic per-student or whole-class brief, explicitly built to replace ad-hoc Zalo messages). Both are real previously-deployed skills for Vietnamese K12 homeroom teachers. Per the owner's consolidation direction, prior system's ~63 over-fragmented folders are being merged into fewer, more practical skills — `parent_letter` and `parent_brief` differ only in cadence/format, not in the underlying task, so they collapse into one skill here.

This was explicitly judged **in-scope** for the Teacher tier (unlike prior system's bureaucratic-paperwork skills — annual reports, correspondence logs, directive letters, meeting minutes, school decisions — which the owner directed be excluded entirely). Writing to parents is core homeroom-teacher work, not school-administration process.

This is a **lighter-structure, tone/completeness-driven** skill, unlike `lesson-plan-builder` or `assessment-builder`, which validate against a strict regulatory structure (CV 5512, TT27/TT22). A parent letter has no equivalent legally-mandated structure — the domain knowledge here is soft: the shape of fields a complete message needs, and a small set of real failure modes worth catching mechanically. This skill doesn't manufacture rigor that doesn't exist in the domain.

## What domain knowledge this validator encodes

Both source prior system skills converge on the same required shape for a complete message home, regardless of cadence:

- **Purpose** — what this communication is for (meeting invite, result notice, cooperation request, reminder, periodic update). Both skills required this be picked/stated explicitly at planning time.
- **At least one concrete content point** — the actual information being conveyed (`body_sections` here; `sec_thu.md` free text in `parent_letter`, the 3-part Học tập/Thái độ/Sự việc block in `parent_brief`).
- **A concrete requested action, or an explicit absence of one** — both skills required "what should the parent do" to be answered, even if the answer is nothing (a pure FYI). A stated-but-vague or placeholder requested_action is worse than none, because it reads as a real ask the parent then can't act on.
- **Sender identity** — name and title, since both skills treat sender attribution (GVCN vs. nhà trường) as load-bearing for how formal/personal the message reads.
- **The single-student-name failure mode is real, not manufactured.** `parent_letter` explicitly warns against sending a form letter with the student-name placeholder unreplaced; `parent_brief`'s `individual` mode is built around exactly one student per file for privacy reasons. A message scoped to a single student with an unfilled name placeholder is a genuine, previously-identified, embarrassing mistake — this is the one hard-block this skill treats as unconditionally disqualifying beyond the generic required-field checks.
- **Tone constraints both skills state explicitly**: respectful and clear, not bureaucratic-stiff and not casual; no exaggeration ("xuất sắc"/"vô cùng"/"rất tệ" in `parent_brief`'s own wording); describe the event, don't judge the student's character; `parent_brief` explicitly forbids "buộc tội / phán xét nhân cách HS" (accusing / character-judging the student) and routes real disciplinary matters to the school's actual disciplinary process, not the parent-communication channel. The harsh/accusatory-language lexicon in this validator is a direct, if necessarily partial, encoding of that constraint.

## How to run

```bash
python scripts/validate_parent_message.py <message.json>
```

Start from `assets/parent_message_template.json`. It has 9 fields:

| Field | Meaning |
| --- | --- |
| `message_type` | `"letter"` (one-off) or `"periodic_brief"` (weekly/monthly). |
| `recipient_scope` | `"single_student"` or `"whole_class"`. |
| `purpose` | Free text: what this communication is for. |
| `student_name_or_placeholder` | The student's name if `recipient_scope` is `single_student`; leave `""` if `whole_class`. |
| `body_sections` | List of the actual content points (at least 1 non-empty item required). |
| `requested_action` | What the parent needs to do, if anything — `""` is a valid, explicit "nothing to do." |
| `sender_name` / `sender_title` | Who is sending this and in what capacity. |
| `contact_info` | How the parent can reply — leave empty rather than inventing one. |

Exit 0 = passes (warnings, if any, print above the VALID line — they're tone signals worth reading, not blocking). Exit 1 = at least one error (missing/empty required field, unresolved placeholder anywhere in the record, or — the hard-blocked case — a `single_student` message with an unfilled/placeholder student name). Exit 2 = file not readable or malformed JSON.

## What this skill does NOT do

- **Does not generate the message content.** No LLM/AI call, ever (per this project's standing rule — Scriptorium skills never integrate an AI backend). A human or an agent writes `purpose`/`body_sections`/`requested_action` first; this only checks the filled-in record before it goes out.
- **Does not judge writing quality, persuasiveness, or whether the content is actually true/appropriate** — it checks completeness and a narrow, mechanical tone lexicon, nothing else. A message can pass this validator and still be a bad message.
- **Does not render a `.docx`.** Delegate that to `office-doc-creator` once the JSON record passes validation — same division of labor as `lesson-plan-builder`.
- **Does not cover school-administration paperwork** (reports, decisions, correspondence logs, meeting minutes) — deliberately out of scope for this tier, per the owner's direction that excluded prior system's bureaucratic-paperwork skills.
- **Does not enforce the two source skills' Vietnamese formal-letter formatting conventions** (Quốc hiệu/Tiêu ngữ header block, 2-column government letterhead, PascalCase filenames) — those are `office-doc-creator` rendering concerns, not completeness/tone concerns, and out of scope here.

## Verified

A complete single-student result-notice letter validated with zero errors/warnings; a letter with an unfilled `<student_name>` placeholder on a single-student message correctly refused (exit 1); a periodic brief with harsh/accusatory language ("hư hỏng", "hỗn láo") about the student correctly warned (exit 0, 2 warnings) without blocking; a message missing `purpose`/`sender_name` correctly refused (exit 1, 2 errors); a whole-class message with an empty (not placeholder) student-name field correctly passed; a `requested_action` left as `<TODO>` correctly refused; malformed JSON and an empty `body_sections` list both correctly refused.

## Known limitations (v0.1.0)

- The accusatory/harsh-language lexicon (`ACCUSATORY_RE`/`PERSONAL_JUDGMENT_RE` in the script) is small and hand-curated, mostly Vietnamese with a few English terms carried over from `peer-review`'s pattern. It will miss paraphrased harshness and will not catch every real tone problem — read it as a tripwire for the most common blunt phrasings, not a complete tone judge.
- Placeholder detection reuses `peer-review`'s exact pattern (`<TODO>`, `[TODO]`, `{{...}}`, `TBD`, `XXX`, bare `<...>` tokens) verbatim. A placeholder written in an unrecognized style (e.g. `___FILL_IN___`) will not be caught.
- No cross-check that `requested_action` content is actually consistent with `message_type` (e.g. a meeting-invite letter with no time/place mentioned anywhere in `body_sections`) — `parent_letter`'s own SKILL.md required time+place for meeting invites specifically, but this validator does not special-case by `purpose` text; it only checks that *something* concrete was requested, not that the right thing was requested for this message type.
- `periodic_brief`'s `summary` (whole-class pivot table) mode from the original prior system skill has no structural equivalent here — `body_sections` is a flat list regardless of `recipient_scope`, so a whole-class summary's per-student rows are not individually validated (e.g. no check that every student in a roster has a row). If real use shows this gap matters, a future version could add a `roster`-aware structure.
