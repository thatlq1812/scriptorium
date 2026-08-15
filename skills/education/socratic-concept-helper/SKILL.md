---
name: socratic-concept-helper
description: 'PAUSED 2026-07-29 (thatlq1812 decision, not production-ready, see Known limitations) -- do not deploy." Instructs the calling agent to help a K12 student understand a concept through guiding questions rather than a direct final answer to a stated homework/graded problem (Khan Academy Khanmigo''s public "Socratic restraint" pattern). Bundles `check_restraint.py`, a deterministic text-pattern linter checking a DRAFTED response for restraint violations -- giveaway final-answer phrasing, zero guiding questions, a leaked arithmetic result. Do NOT use this to generate the tutoring response itself; do NOT treat a clean lint run as proof of genuine restraint -- see "Known limitations".'
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, ast, re) -- no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N3
  source: self-authored
  elicited_from: "General-capability tier per CLAUDE.md principle 4 (education/pedagogy knowledge is publicly documented, not tacit) -- grounded directly in outside_research/research_02/research_02_result_01.md's real 2025-2026 secondary research (already gathered this project, not re-derived here): College Board Oct 2025 (84% of US high-schoolers use generative AI for schoolwork), PEW 2025 (half of US teens use chatbots for schoolwork help), a faculty survey (92% concerned about AI-facilitated academic dishonesty), and arXiv:2605.21629 ('Faster Completion, Less Learning', 2026) showing generative-AI use measurably reduced both study time AND retained knowledge on math problems -- the quantified real-world risk this skill's restraint gate exists to mitigate. The behavioral design pattern itself -- never answer directly, ask a guiding question, trade immediate correctness for productive struggle -- is Khan Academy Khanmigo's publicly documented Socratic-tutoring approach (cited in the same research brief: 'AI Socratic Tutors: Teaching The World To Think', aicompetence.org; 'Khanmigo: Khan Academy's AI Tutor', tooldirectory.ai). The curriculum anchor (this is not just risk-avoidance but serves an actual mandated competency) is CT GDPT 2018 / Thong Tu 32/2018/TT-BGDDT's 'nang luc tu chu va tu hoc' (self-directed learning), one of exactly 3 'nang luc chung' the Vietnamese national curriculum is built to develop, already cited by lesson-plan-builder's competency vocabulary. NOTE for the registering session: docs/specs/STRATEGY_SPEC.md section 5.1's own research brief (research_02_result_01.md section 7) flags this exact candidate as needing a real student/teacher survey before a skill-creator run -- this build proceeds on direct thatlq1812/orchestrator instruction (2026-07-29 task dispatch) treating it as general-capability-tier (public pedagogy pattern, not a tacit niche-specializer process) rather than waiting on that survey; flagging the discrepancy for the registering session to reconcile against STRATEGY_SPEC's own stated bar, not resolving it unilaterally here."
  version: 0.1.0
  grounding: optional
  object_type: ["tutoring-response"]
---

# socratic-concept-helper

> [!WARNING]
> **PAUSED (thatlq1812 decision, 2026-07-29) — not recommended for production use.** `skill-exporter` refuses to export this skill (`registry/skills.json`'s `operational_status.state == "paused"`). Two reasons, both real: (1) built ahead of `docs/specs/STRATEGY_SPEC.md`'s own recommendation for a real student/teacher survey — a follow-up `deep-research` round confirmed public-source research does not substitute for it (`outside_research/research_06_socratic_helper/research_brief.json`); (2) a structural mismatch — this skill assumes a K12 student directly operates an agent harness in real time, which doesn't match how K12 students actually use AI (chat apps, not agent CLIs). See `docs/DECISIONS_PENDING.md`'s resolved item 5 for the full record. The code below is left in place because `check_restraint.py`'s mechanical linter may be reusable once a real operator model (teacher/tutor-mediated) is settled — not because the skill is ready as-is.

A behavioral skill: it instructs the calling agent HOW to converse with a K12 student about a concept -- through guiding questions, never a direct final answer to a stated homework/graded problem. The only script component is a deterministic LINTER that checks a drafted response for restraint violations before it's sent, mirroring this repo's "script decides pass/fail mechanically, not a model's judgment call" discipline (CLAUDE.md "Working with skills"). It never calls an LLM/AI API itself.

## Why this skill, and why this scope

`outside_research/research_02/research_02_result_01.md` (real secondary research already done this project) found the central real risk for the Student (K12) tier: generative AI that answers a student's question directly is not a smaller-stakes version of some other risk, it is a documented, currently-measured harm to the learning outcome the tool claims to support (arXiv:2605.21629 found reduced study time AND reduced retained knowledge, not just an academic-integrity problem). The same brief identified the resolving design pattern already proven at scale: Khan Academy Khanmigo's Socratic restraint -- never answer directly, always nudge toward the student's own reasoning.

A prose instruction alone ("be Socratic, don't give the answer") is exactly the kind of thing a model can drift from under pressure (a student insisting, a long conversation, an ambiguous question). Per this repo's gate-pattern precedent (`peer-review`'s mandatory intake gate, `hypothesis-generation`'s confirmed-status gate, the research brief's own explicit recommendation in section 4), this skill adds a mechanical check on top of the prose instruction: a script that reads a DRAFTED response and flags the cheapest, most common ways restraint gets broken, before that response reaches the student.

## The behavioral instruction (for the calling agent)

When a K12 student asks about a concept, especially one that reads as a stated homework/graded/exam-style question:

1. Never state the final numeric/textual answer to the stated problem, and never provide an answer key, up front or at all, unless the student has already shown genuine, complete work and is asking you to check (not produce) their own answer.
2. Always respond with at least one guiding question that nudges the student toward their own next step ("what have you tried?", "what's the first thing you'd need to know?", "what does this term mean to you so far?").
3. It is fine, and often better, to explain a *concept* in general (what a technique is, why it works, an analogous simpler example) -- restraint applies to the answer of the STATED problem, not to teaching the underlying idea.
4. Before sending a drafted response to the student, run it through `check_restraint.py` (below). A flagged violation means revise before sending -- don't override the linter's finding without a specific, stated reason (e.g. the student has already fully solved it and is asking for confirmation, which is a legitimate exception to rule 1).

## Run

```bash
python scripts/check_restraint.py <session.json>
```

Start from `assets/session_template.json`:

```json
{
  "student_message": "What is 12 * 15 for my homework problem?",
  "draft_response": "Good question -- before we get to a number, what's one way you already know to break 12 * 15 into smaller, easier pieces?",
  "context": "homework"
}
```

`context` is optional (`"homework"` | `"exam"` | `"general"`, default `"general"`) -- recorded for the report, does not change which checks run (the same mechanical checks apply regardless of context; a violation in a homework/exam context should be treated as higher priority by whoever reviews it).

Checks performed, all deterministic text-pattern matching:

1. **Giveaway final-answer/answer-key phrasing** -- a curated, literal, case-insensitive phrase list (`"the answer is"`, `"final answer:"`, `"the correct answer is"`, `"answer key"`, `"solution:"`, etc.).
2. **Zero guiding questions** -- the draft response contains no `?` at all.
3. **Literal computed-arithmetic-answer leak** -- if the student's message contains a simple arithmetic expression (numbers and `+ - * /` only), the script extracts and evaluates it itself using a restricted `ast`-based evaluator (never `eval()`/`exec()`), then checks whether that exact computed value appears as a standalone number in the draft response. This is the one check that is genuinely provable, not a phrase-list guess.

Exit 0 = no known violation pattern found, exit 1 = one or more violations (each printed with the exact matched text/reason), exit 2 = malformed input (missing/empty `draft_response`, missing/non-string `student_message`, invalid `context`, bad JSON).

## What this skill does NOT do

- Does not generate the tutoring response itself -- no LLM/AI call of any kind, per this project's no-AI-backend principle (CLAUDE.md principle 8). The calling agent drafts the response using its own judgment and the behavioral instruction above; this skill only lints the draft afterward.
- Does not understand semantics -- it cannot detect a paraphrased final answer that avoids every giveaway phrase (e.g. "yep, twelve times fifteen works out to a number in the low 200s, specifically one hundred eighty" dodges the literal phrase list while still giving away the answer in prose), an answer embedded naturally inside an otherwise-Socratic-sounding worked derivation, or a non-arithmetic final answer (a vocabulary definition, a historical date, a chemistry formula) stated outright. These are real, known gaps -- see "Known limitations".
- Does not detect restraint violations across a multi-turn conversation -- each call lints one `(student_message, draft_response)` pair in isolation; a student wearing the agent down over several turns until it caves on turn 5 is not visible to a single lint call.
- Does not decide whether an exception to rule 1 (student has already solved it, is asking for confirmation) legitimately applies -- that judgment stays with the calling agent; the linter only flags the mechanical pattern, a human/agent decision can still override it with a stated reason.
- Does not call any network/LLM service to do the checking -- pure stdlib text-pattern and restricted-arithmetic evaluation, exactly per the task's explicit instruction to keep this deterministic and honest about scope.

## Verified

Ran `check_restraint.py` against `assets/session_template.json` (the bundled valid example: guiding question, no giveaway phrasing, no leaked arithmetic answer) -- exit 0, "OK: no known restraint-violation pattern found."

Deliberately broken cases run for real, each producing the exact expected violation(s):

- **Direct giveaway phrase**: `draft_response: "The answer is 180."` against `student_message: "What is 12 * 15?"` -- exit 1, flagged BOTH the giveaway-phrase match (`'the answer is'`) AND the literal-arithmetic-leak check (180 = 12*15, found as a standalone token in the response).
- **Zero-question response with an explanation but no final phrase or leaked number**: `draft_response: "Multiplication is repeated addition, so you're adding twelve to itself fifteen times in total."` (contains no `?`, no giveaway phrase, no literal 180 in the text) -- exit 1, flagged only the "no question mark" violation, confirming the checks are independent and don't over-trigger on each other.
- **Answer-key phrase without an underlying arithmetic problem**: `student_message: "What's the capital of France?"`, `draft_response: "The correct answer is Paris. Answer key: Paris is the capital of France."` -- exit 1, flagged both `'the correct answer is'` and `'answer key'` giveaway matches; correctly did NOT attempt (and did not crash on) the arithmetic-leak check since no arithmetic expression exists in the student message.
- **Legitimate Socratic response passes even with a question late in a long response**: `draft_response: "Twelve times fifteen looks like a big multiplication, but you already know how to multiply by ten and by five separately -- what do you get if you first compute 12 * 10, then separately 12 * 5?"` -- exit 0. Confirmed the linter does not flag the literal digits "12", "10", "5" (none equal the final computed answer 180) and correctly treats a response that breaks the problem into sub-steps via a question as passing, not a violation.
- **Malformed input**: a JSON file that is a bare array (`[1, 2, 3]`) instead of an object -- exit 2, "must contain a JSON object". A JSON object missing `draft_response` entirely -- exit 2, naming the missing/required field. A JSON object with `draft_response: ""` (empty string) -- exit 2, correctly refused as empty rather than treated as a trivially-passing response. An invalid `context: "vacation"` -- exit 2, naming the invalid value and the allowed set. A file with syntactically broken JSON (trailing comma) -- exit 2, "malformed JSON" with the underlying `json.JSONDecodeError` message.
- **Safe-eval boundary check**: `student_message: "What is 12 * 0?"` -- verified the restricted AST evaluator correctly computes `0` and the literal-leak check correctly matches a standalone `"0"` in a deliberately bad draft response (`"The answer is 0."`, exit 1, both the giveaway-phrase and the arithmetic-leak violations fired). Also verified the digit-boundary regex (`(?<!\d)...(?!\d)`) correctly does NOT match "0" as a substring of a longer number like "100" -- but a follow-up case (`draft_response: "...over 100 students answered this... what pattern do you notice about multiplying by 0?"`) surfaced a real, honest gap: because the computed answer (0) happens to equal a factor already present in the student's own question, the standalone "0" in "multiplying by **0**?" (a legitimate re-mention of the problem's own operand inside a guiding question, not an answer leak) still matches and produces a false-positive violation. This is now documented as a known limitation below rather than papered over.

## Known limitations (v0.1.0)

- **Cannot catch a paraphrased final answer.** The giveaway-phrase list is literal and finite; a response that states the answer in different wording entirely dodges it. This is a fundamental limit of text-pattern matching without an LLM call, and this project never makes an LLM call from a skill script (CLAUDE.md principle 8) -- so this gap is permanent for this design, not a bug to fix later. The calling agent's own judgment remains the primary safeguard; the linter is a cheap second check, not a replacement for it.
- **Cannot catch an answer embedded naturally inside an otherwise-Socratic-sounding derivation** that never uses a giveaway phrase and never leaves the literal final number as an isolated token (e.g. spelled out in words, or split across a sentence).
- **The arithmetic-leak check can false-positive when the computed answer coincides with a number already present in the student's own question** (e.g. `12 * 0` computes to `0`, and a guiding response that legitimately re-mentions "multiplying by 0" as part of the question -- not as an answer -- still matches the standalone-`0` check). Found during real testing this session, not a hypothetical -- see "Verified" above. A human/agent reviewing a flagged violation should read the matched context, not treat every flag as certainly a real leak.
- **The arithmetic-leak check only covers `+ - * /` on plain numbers** -- no exponents, roots, percentages, fractions, algebra (variables), or multi-step word problems. A non-arithmetic final answer (a vocabulary term, a formula, a historical fact) is entirely outside what this script can verify computationally; only the phrase-list and zero-question checks apply to those.
- **No cross-turn/conversation-level memory.** Each call lints exactly one message/response pair; a restraint violation that only emerges from the pattern of several turns (agent giving progressively bigger hints until turn N is effectively the answer) is invisible to a single call.
- **No real student/teacher survey exists for this tier yet** (see `metadata.elicited_from` above) -- this skill's design is grounded in public secondary research (Khanmigo's published pattern, the cited 2025-2026 studies) per CLAUDE.md's general-capability-tier bar, not a practitioner interview. `docs/specs/STRATEGY_SPEC.md`'s own Student-tier research brief flags this candidate as the one that "needs a real student/teacher survey... strongly" before `skill-creator` runs; this build proceeded on direct orchestrator instruction treating it as general-capability grounding instead. Flagged explicitly for the registering session to reconcile, not silently resolved here.
- **Follow-up deep-research round (2026-07-29), same day, thatlq1812-directed**: `outside_research/research_06_socratic_helper/research_brief.json` (validated via `skills/general/deep-research`) explicitly tested whether further public-source research could close this gap. It did not -- if anything it reinforces the original recommendation: even Khan Academy's well-resourced Khanmigo only achieves ~15% regular student usage (adoption/engagement, not just answer-leakage, is the dominant real-world risk, and this skill's linter has no mechanism for that at all); current AIED research names "empowering teachers" a core design principle, not optional; and Vietnam's own Ministry of Education is explicitly staging its 2025-2026 AI-in-schools rollout as a measured pilot, naming teacher capacity a co-equal prerequisite. No source answers the one question that actually matters here -- how real Vietnamese K-12 students/teachers would experience this exact restraint design. See `docs/DECISIONS_PENDING.md` item 1 for the full brief and the still-open recommendation to commission a real survey/pilot.
