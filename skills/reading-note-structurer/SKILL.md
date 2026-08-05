---
name: reading-note-structurer
description: 'Validates/renders a Cornell-notes or mind-map-style structured reading note -- `validate_note.py` checks that a note declared `"type": "cornell"` has a non-empty title, at least one cue/notes entry pair (both non-empty), and a non-empty summary; a note declared `"type": "mindmap"` has a non-empty central_topic and at least one branch, with every branch (recursively, any depth) having a non-empty label -- then renders the validated note to clean Markdown. Use when a student has already written down reading/lecture notes in one of these two structures and wants them checked for missing pieces before relying on them to study, or rendered to a clean Markdown file. Do NOT use this to generate note content, summarize a source text, or judge whether the captured content is accurate/complete relative to the source -- the caller always supplies every cue, note, summary line, and branch label; this validates structural completeness only.'
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "General-capability tier per CLAUDE.md principle 4 -- both note structures are publicly documented, established study methods, not tacit knowledge. Cornell Notes is Walter Pauk's real, publicly documented note-taking method (Cornell University's Learning Strategies Center, 'How to Study in College') -- the cue-column/note-taking-column/summary three-part structure encoded here (entries[].cue, entries[].notes, summary) is that method's actual documented shape, not invented. Mind mapping's branching central-topic structure is Tony Buzan's publicly documented technique, widely taught as a K12 study/note-organization method. Structural-validator shape (caller supplies all content, script checks required fields present/non-empty, then renders to Markdown) mirrors competency-rubric-builder's validate_rubric.py (D:/elix/scriptorium/skills/competency-rubric-builder/SKILL.md) -- same 'never judge content quality, only structural completeness' discipline, applied to a student's own reading notes instead of a teacher's rubric."
  version: 0.1.1
  changelog_0_1_1: "Doc-only: added a 'Who operates this' section clarifying the operator model after the Student(K12)/University Student tier merge (2026-07-29, docs/DECISIONS_PENDING.md resolved item 6) -- no script/behavior change."
  grounding: not_applicable
  object_type: ["reading-note"]
---

# reading-note-structurer

Validates a Cornell-notes or mind-map-style structured note, then renders it to clean Markdown. Pure structural checking -- it never writes, summarizes, or judges the accuracy of a single word of note content; the student (or teacher) supplies everything, this only checks the required pieces are actually there.

## Who operates this (2026-07-29 clarification -- Student/Learner tier merge, `docs/DECISIONS_PENDING.md` resolved item 6)

Student (K12) and University Student merged into one Student/Learner tier -- skill shape doesn't differ by age, who realistically drives the agent does. A university/adult self-directed learner can plausibly run this themselves. A K12 student almost never operates an agent harness directly (they use a chat app, not an agent CLI) -- realistically a teacher/tutor checks the note structure on the student's behalf, or a parent helps at home. Either way the tool's contract is the same: content always caller-supplied, structure always checked mechanically.

## Why this skill, and why this scope

Cornell Notes (Walter Pauk, Cornell University) and mind mapping (Tony Buzan) are both real, publicly documented, widely taught K12 study methods -- not tacit or niche knowledge, so this qualifies for the general-capability elicitation bar (CLAUDE.md principle 4) directly from their public documentation rather than needing an expert interview. Both share a real, common failure mode this skill targets: a student who half-fills a note structure (a cue with no notes written under it yet, a mind-map branch with a label but nothing captured, no summary written at the end of a Cornell page) ends up with a study artifact that LOOKS complete but has silent gaps -- exactly the kind of thing a deterministic structural check catches cheaply, before the student relies on it later to review.

Like `competency-rubric-builder` (the closest sibling in this repo -- a structural validator for a teacher's rubric, never judging pedagogical quality), this skill draws a hard line at structure: it checks a cue exists and a note exists under it, never whether the note correctly captures what the cue is asking about.

## The two supported structures

### Cornell (`"type": "cornell"`)

- `title` (required, non-empty) -- the note's subject/heading.
- `topic`, `date` (optional) -- rendered if present, not validated against any format.
- `entries` (required, non-empty list) -- each entry is one cue/notes row: `cue` (the recall question/keyword) and `notes` (the actual content captured for it), both required and non-empty.
- `summary` (required, non-empty) -- the bottom-of-page synthesis, Cornell Notes' defining third section beyond the two-column cue/notes area.

### Mind map (`"type": "mindmap"`)

- `title` (optional; falls back to `central_topic` if absent) -- rendered heading.
- `central_topic` (required, non-empty) -- the map's center node.
- `branches` (required, non-empty list) -- each branch is `{"label": "...", "children": [...]}`. `children` may be an empty list (a leaf branch) or a list of further branches, recursively, to any depth -- every branch at every depth must have a non-empty `label`.

## Run

```bash
python scripts/validate_note.py <note.json> [--render note.md] [--force]
```

Start from `assets/cornell_note_template.json` or `assets/mindmap_note_template.json` depending on which structure you're using. Exit 0 = structurally valid (stdout confirms the type); exit 1 = one or more violations, each printed with the exact field/path (e.g. `entries[2].notes`, `branches[0].children[1].label`); exit 2 = malformed input, an unrecognized/missing `type`, or `--render` target already exists without `--force`. `--render` only writes output when there are zero errors.

## What this skill does NOT do

- Does not generate, summarize, or paraphrase any note content -- no LLM/AI call of any kind. The student (or teacher) writes every cue, note, summary line, and branch label; this only checks the required structural pieces are present.
- Does not judge whether a cue's notes actually answer that cue, whether a summary genuinely synthesizes the entries above it, or whether a mind-map branch's placement/grouping makes conceptual sense -- pure presence/non-emptiness checking, same structural-only stance as `competency-rubric-builder`.
- Does not check content against any source text (a textbook chapter, a lecture transcript) for completeness or accuracy -- it has no access to and makes no claim about the original source; a note can pass validation and still have missed something important from the source material.
- Does not support other note formats (outline notes, the Charting method, boxing method) in v0.1.0 -- only Cornell and mind-map, per the task's explicit scope; see "Known limitations."
- Does not render to `.docx`/PDF -- delegate the validated Markdown to `office-doc-creator` if a printable document is needed.

## Verified

`validate_note.py` against `assets/cornell_note_template.json` (3 entries, summary present) with `--render`: exit 0, "OK: cornell note is structurally valid," Markdown written and manually inspected -- correct H1 title, Topic/Date metadata line, a clean `| Cue | Notes |` table with all 3 rows, and a `## Summary` section with the summary text. Re-running with `--render` pointed at the same path without `--force` -- exit 2, correctly refused; with `--force` -- correctly overwrote.

`validate_note.py` against `assets/mindmap_note_template.json` (3 top-level branches, one nested 2 levels deep -- "Location" > "Chloroplast" > "Thylakoid (light reactions)"/"Stroma (Calvin cycle)") with `--render`: exit 0, Markdown rendered and manually inspected -- correct nested bullet indentation confirmed for all 3 depth levels, including the depth-2 leaf labels under "Chloroplast."

Deliberately broken cases run for real:

- Cornell note with `entries: []` (empty list) -- exit 1, "'entries' must be a non-empty list."
- Cornell note with one entry missing `notes` entirely (`{"cue": "..."}`  only) -- exit 1, named exactly `entries[0].notes is missing or empty.`
- Cornell note with `summary: ""` (empty string) -- exit 1, correctly refused (not silently treated as absent-but-ok).
- Cornell note missing `title` entirely -- exit 1, `'title' is required and must be a non-empty string.`
- Mind map with `branches: []` -- exit 1, "'branches' must be a non-empty list."
- Mind map with a depth-2 nested child missing its `label` (`{"children": [{"label": ""}]}` two levels down) -- exit 1, correctly named the exact nested path `branches[0].children[1].label is missing or empty.`, confirming the recursive check reaches arbitrary depth, not just the top level.
- Mind map with `central_topic` missing -- exit 1, named exactly.
- A note with `"type": "outline"` (unsupported type) -- exit 2, naming the invalid type and the two supported values.
- A note missing `type` entirely -- exit 2, same message (`None` reported as the invalid type).
- Malformed JSON (missing closing brace) -- exit 2, `json.JSONDecodeError` message surfaced.
- A JSON array (`[1, 2, 3]`) instead of an object -- exit 2, "must contain a JSON object, got list."
- A mind-map branch where `children` is a string instead of a list -- exit 1, correctly named `branches[0].children must be a list (may be empty), got str.` rather than crashing when the recursive validator tried to iterate it.

## Known limitations (v0.1.0)

- **Only Cornell and mind-map structures.** Other real, publicly documented note-taking methods (outline method, Charting method, boxing/matrix method, the Feynman-technique explanation format) are out of scope for v0.1.0, per the task's explicit two-structure scope. A future version could add more `type` values following the same "caller supplies content, script checks required fields" pattern.
- **No duplicate-label or duplicate-cue detection.** Unlike `competency-rubric-builder`'s copy-paste-description warning, this skill does not flag a mind-map branch reusing the same label twice, or a Cornell cue repeated verbatim -- a deliberate v0.1.0 simplification since duplication in a note (unlike a rubric) isn't necessarily a quality problem (the same keyword can legitimately recur across different sections of a reading).
- **No source-material cross-check.** This skill has no mechanism to verify a note's content against the actual textbook/lecture it summarizes -- validated structure says nothing about whether important content was missed. A student's note can pass this check and still be an incomplete summary of the source.
- **Mind-map recursion has no depth or branch-count cap.** A pathological input (thousands of nested levels) is not specifically guarded against; not expected to matter for a real student's hand-authored note, flagged for completeness rather than as a known real-world problem.
