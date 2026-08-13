---
name: exam-ready-scaffold
description: Deterministic flashcard/quiz-item builder from a caller-supplied topic/fact list -- `build_deck.py` turns a list of {term, definition} facts into flashcards and/or 4-choice MCQ items whose distractors are OTHER real definitions from the same supplied list (never a fabricated wrong answer), selected and ordered by a fixed rule (no randomness, same input always produces the same output); `validate_deck.py` structurally checks a deck (hand-authored or generated) for missing fields, duplicate terms, wrong choice counts, and an answer label that doesn't point at a real choice. Use when a student/teacher has a topic's facts already written down and wants them turned into study-ready flashcards/quiz items, or wants a drafted deck checked before use. Do NOT use this to invent facts, definitions, or distractor content that the caller didn't supply -- every word of the substantive content (term, definition, distractor text) traces back to the caller's own facts.json; this skill only reshapes and validates structure.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: drafting
  risk_tier: N1
  source: self-authored
  elicited_from: "General-capability tier per CLAUDE.md principle 4 -- flashcard/retrieval-practice study tools are publicly documented pedagogy, not tacit knowledge. Grounded in outside_research/research_02/research_02_result_01.md section 5's real cited effect-size research on retrieval practice (Rowland 2014 meta-analysis, g ~= 0.50 for retrieval practice vs. re-reading; Latimier et al., g ~= 0.74 for spaced vs. massed retrieval practice) -- the same research brief that already grounds study-plan-builder's spaced-scheduling mechanism, applied here to the content-item shape (flashcard/MCQ) study-plan-builder deliberately left opaque ('a session is an opaque unit'). Structural posture (structure/validate content the caller supplies, never generate substantive content) mirrors assessment-builder's build_exam_matrix.py/validate_exam.py split (D:/elix/scriptorium/skills/education/assessment-builder/SKILL.md) -- same 'no LLM call, ever; a human or the calling agent supplies real content' discipline, scoped down from assessment-builder's full cognitive-level exam-matrix balancing to a simpler flashcard/MCQ-from-a-fact-list case appropriate for a student building their own study materials rather than a teacher building a formal exam."
  version: 0.1.1
  changelog_0_1_1: "Doc-only: added a 'Who operates this' section clarifying the operator model after the Student(K12)/University Student tier merge (2026-07-29, docs/DECISIONS_PENDING.md resolved item 6) -- no script/behavior change."
  grounding: not_applicable
  object_type: ["flashcard", "quiz-item"]
---

# exam-ready-scaffold

Turns a caller-supplied list of `{term, definition}` facts into flashcards and/or 4-choice MCQ items, and validates a deck's structure. Two deterministic, stdlib-only tools -- no AI/LLM call anywhere in this skill, and no content (term, definition, or distractor text) is ever invented; everything traces back to what the caller supplied.

## Who operates this (2026-07-29 clarification -- Student/Learner tier merge, `docs/DECISIONS_PENDING.md` resolved item 6)

Student (K12) and University Student merged into one Student/Learner tier -- skill shape doesn't differ by age, who realistically drives the agent does. A university/adult self-directed learner with agent-CLI access can plausibly run this themselves. A K12 student almost never does (they use a chat app, not an agent harness), so for that age group the realistic operator is a teacher/tutor preparing a deck FOR students, not the student self-generating it mid-study-session. The skill's input/output contract is unchanged either way -- this only affects who it's built and distributed for.

## Why this skill, and why this scope

`outside_research/research_02/research_02_result_01.md` section 5 confirms retrieval practice (recalling a fact rather than re-reading it) has a strong, replicated effect size, and flags "review of caller-supplied flashcard/question decks" as the safest, lowest-elicitation-risk next step for the Student (K12) tier -- the mechanism `study-plan-builder` already schedules but deliberately leaves the actual study-item content opaque ("a session is an opaque unit ... doesn't account for topics needing meaningfully different amounts of time"). This skill fills that one gap: turning a fact list into study-ready items, without ever crossing into generating the facts themselves.

The design constraint from the same research brief (§3: generative AI that does content generation on a student's behalf is a documented harm to the exact learning outcome it claims to help) rules out ever inventing a definition or a "plausible enough" wrong answer for an MCQ distractor. So the distractor-selection rule here is deliberately narrow: an MCQ item's 3 wrong choices are always OTHER facts' real, caller-supplied definitions from the same list -- never fabricated text. This mirrors `assessment-builder`'s hard line ("no LLM call, ever ... this skill only balances and validates structure/numbers") applied to the simpler flashcard/MCQ case.

## Run

### 1. Build a deck from a fact list

```bash
python scripts/build_deck.py <facts.json> --mode {flashcards,mcq,both} -o deck.json [--force]
```

Start from `assets/facts_template.json`:

```json
{
  "topic": "Cell biology",
  "facts": [
    {"term": "Mitochondria", "definition": "The organelle that produces ATP through cellular respiration."},
    {"term": "Nucleus", "definition": "The organelle that houses the cell's genetic material."}
  ]
}
```

- `--mode flashcards` -- one flashcard per fact (`{term, definition}`), same order as input.
- `--mode mcq` -- one 4-choice item per fact: `question` is a fixed template (`"Which definition matches '<term>'?"`), the correct choice is that fact's own definition, and the 3 distractor choices are the definitions of the NEXT 3 facts in list order (wrapping around, skipping the fact itself) -- real content, never invented. Choice position and the resulting `answer` label are placed by a fixed deterministic rule keyed on the fact's own index (not randomness) -- the same input always produces the same output, every run. **Requires at least 4 facts** (fewer than 4 means there aren't enough real definitions to fill 3 distinct distractor slots) -- refused with exit 1 naming the shortfall if requested with fewer.
- `--mode both` (default) -- both of the above.

Exit 0 = deck written (stdout echoes the counts); exit 1 = valid input but `mcq` mode requested with fewer than 4 facts; exit 2 = malformed input, or output path exists without `--force`.

### 2. Validate a deck's structure

```bash
python scripts/validate_deck.py <deck.json>
```

Works on `build_deck.py`'s own output or a hand-authored deck following the same schema. Checks:

- at least one of `flashcards` / `mcq` is present and non-empty;
- every flashcard has non-empty `term` and `definition`, no duplicate term (case/whitespace-insensitive);
- every MCQ item has a non-empty `question`, exactly 4 distinct non-empty `choices`, and an `answer` label (`"A"`-`"D"`) that actually corresponds to one of the 4 choices.

Exit 0 = structurally valid; exit 1 = one or more violations, each named with the exact index/field; exit 2 = malformed input.

## What this skill does NOT do

- Does not invent facts, definitions, or distractor text -- every substantive word in a generated flashcard or MCQ choice comes from the caller's own `facts.json`; no LLM/AI call of any kind, per this project's no-AI-backend principle.
- Does not judge whether a definition is factually correct, whether a distractor is a "good" (plausible but wrong) choice, or whether the fact list is complete/exam-relevant for any real curriculum -- pure structural reshaping and validation, same posture as `study-plan-builder`'s "doesn't validate that the topic list itself is ... exam-relevant."
- Does not do spaced-repetition scheduling itself -- that's `study-plan-builder`'s job; this skill only produces the study-item content that a scheduler like it would resurface over time. The two are meant to compose, not duplicate each other.
- Does not render a printable `.docx`/PDF deck -- delegate to `office-doc-creator` once a deck passes `validate_deck.py`.
- Does not support fill-in-the-blank, matching, or true/false item types in v0.1.0 -- only flashcards and classic 4-choice MCQ; see "Known limitations."

## Verified

`build_deck.py` against the bundled `assets/facts_template.json` (5 facts, topic "Cell biology"), `--mode both`: exit 0, wrote 5 flashcards and 5 MCQ items; manually checked each MCQ item's 3 distractor definitions were real definitions from OTHER facts in the list (never invented text), each item had exactly 4 distinct choices, and the labeled `answer` position actually held that fact's own correct definition -- verified for all 5 items, correct-answer positions correctly rotated (A, B, C, D, A) rather than always landing in the same slot. Re-ran the exact same command a second time and diffed the two output files -- byte-identical, confirming determinism (no randomness). `--mode mcq` against a deliberately trimmed 3-fact input -- exit 1, "mcq mode requires at least 4 facts ... got 3." `--mode flashcards` against the same 3-fact input -- exit 0 (flashcards mode has no minimum), 3 flashcards written. A `facts.json` with a duplicate term (`"Nucleus"` twice, second entry lowercase `"nucleus"`) -- exit 2, correctly caught by the case/whitespace-insensitive duplicate check naming the exact index. A fact missing `definition` entirely -- exit 2, naming the exact `facts[i].definition` field. Malformed JSON (unterminated string) -- exit 2. Re-running `build_deck.py` against an existing output path without `--force` -- exit 2, correctly refused; with `--force` -- correctly overwrote.

`validate_deck.py` against the `build_deck.py`-generated 5-fact/`both`-mode deck from above -- exit 0, "5 flashcard(s), 5 mcq item(s)." A deck with only `flashcards` (no `mcq` key at all) -- exit 0, correctly treated as valid (at-least-one rule). An empty JSON object `{}` -- exit 1, "deck must contain at least one of 'flashcards' or 'mcq'." An MCQ item with only 3 choices -- exit 1, naming the exact count (3, must have 4). An MCQ item with 4 choices but two identical (case-insensitive) -- exit 1, flagged as duplicate choices. An MCQ item with `"answer": "E"` (out of range for 4 choices) -- exit 1, naming the invalid label and the valid set `['A', 'B', 'C', 'D']`. A flashcard with `"definition": "   "` (whitespace-only) -- exit 1, correctly treated as empty, not a valid value. Malformed JSON and a JSON array instead of an object were both correctly refused (exit 2).

## Known limitations (v0.1.0)

- **Only flashcards and classic 4-choice MCQ** -- no fill-in-the-blank, matching, true/false, or short-answer item types. A future version could add these if real use shows the need, following the same "structure/validate, never invent content" discipline.
- **MCQ distractor selection is a fixed list-order rule (next 3 facts, wrapping)**, not a semantic "plausible wrong answer" selection -- with a small or highly homogeneous fact list, distractors may end up obviously wrong to a student who already knows the topic well (e.g. a distractor from a completely unrelated sub-topic). A future version could accept a caller-declared "distractor pool" grouping if this turns out to matter in real use; not attempted here to avoid inventing a semantic-similarity heuristic this project has no grounding for.
- **`question` text in MCQ mode is a single fixed template** (`"Which definition matches '<term>'?"`) -- not varied by fact type, difficulty, or Bloom's-taxonomy level like `assessment-builder`'s cognitive-level framework. A caller wanting varied question phrasing must post-process the generated deck themselves; this skill does not attempt to.
- **Does not compose automatically with `study-plan-builder`** -- both skills exist and share a design rationale (content-neutral, retrieval-practice-grounded), but no integration/wiring between them has been built or tested this session; a real end-to-end run feeding this skill's deck into `study-plan-builder`'s scheduling hasn't happened yet.
- **`--mode mcq`'s 4-fact minimum is a hard floor, not adjustable** -- a caller with fewer than 4 facts cannot get MCQ items from this tool at all (even a 2-choice or 3-choice item), by design (a 3-choice item drawn from only 2 available real distractors was judged a worse trade-off than refusing outright).
