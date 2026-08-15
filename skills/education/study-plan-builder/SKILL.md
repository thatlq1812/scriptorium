---
name: study-plan-builder
description: Turns a flat list of study topics into a day-by-day study/review schedule — spaces out topics so the same one is never studied twice in a row, and inserts periodic review sessions cycling through everything introduced so far. Use when a student wants to plan how to work through a syllabus/topic list over N days before an exam or deadline. Do NOT use this to answer questions, solve problems, or do the work itself — it only decides WHEN to study WHAT; the studying stays entirely the student's own.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, math) — no dependency, no venv needed, local-only, zero network calls of any kind. Verified running clean: Claude Code (2026-07-26). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "First skill for the 'Student (K12)' audience tier (docs/specs/STRATEGY_SPEC.md §5.1) -- no real student survey exists yet (tracked gap), so this was deliberately scoped to the simplest, least-controversial capability for that tier per thatlq1812 direction (2026-07-26): pure scheduling arithmetic over a topic list, never touching subject content or answering questions, avoiding the 'doing the student's work' ethical line entirely. Candidate name and shape cross-checked against the 'learning-path-planner' idea in outside_research/research_01_lawer-work.md (external AI brainstorm, treated as ideation only, not elicited input) but the algorithm itself (interleaved round-robin new-topics + periodic review-everyone-so-far) is original to this session, not copied from that brainstorm or any external source."
  version: 0.1.1
  changelog_0_1_1: "Doc-only: added a 'Who operates this' section clarifying the operator model after the Student(K12)/University Student tier merge (2026-07-29, docs/DECISIONS_PENDING.md resolved item 6) -- no script/behavior change."
  grounding: not_applicable
  object_type: ["study-plan"]
---

# study-plan-builder

Turns a topic list into a day-by-day study/review schedule. Pure scheduling arithmetic — it never explains, answers, or does any of the actual studying.

## Who operates this (2026-07-29 clarification — Student/Learner tier merge, `docs/DECISIONS_PENDING.md` resolved item 6)

The "Student (K12)" and "University Student" audience tiers merged into one Student/Learner tier — skill *shape* doesn't differ by age, but *who drives the agent* usually does. A self-directed university student or adult learner working with an agent CLI can plausibly run this directly. A K12 student almost never does — they use a chat app, not an agent harness — so for that age group the realistic operator is a teacher, tutor, or parent generating the schedule on the student's behalf (the output is just a schedule; handing a printed/shared version to the student afterward doesn't require the student to touch the tool at all). This skill's own logic doesn't care who runs it — the distinction matters for how the skill gets distributed and who it's marketed to, not for its input/output contract.

## Why this skill, and why this scope

This is the first skill for the **Student (K12)** audience tier (`docs/specs/STRATEGY_SPEC.md` §5.1) — the one tier with no real elicitation source yet (no student survey exists, unlike the Teacher tier which has prior system, or the legal vertical which has a real practitioner survey). Rather than build from an external AI's brainstormed list directly, this was scoped to the single most defensible capability: schedule arithmetic. It carries no risk of "doing the assignment for the student" (a real ethical line for a student-facing tool) and needs zero subject-matter knowledge to be correct, so it doesn't inherit the hallucination risk that content-generating student tools would.

## Algorithm (v0.1.0)

1. Each topic has a `weight` (1-5, default 2) — how many "new-study" sessions it needs.
2. New-topic sessions are interleaved round-robin across all topics with remaining weight, so the same topic is never studied twice in a row while others still need first-time coverage.
3. Every Nth session (`--review-every`, default 4) is a review session, cycling round-robin through every topic introduced so far.
4. If total session capacity (`--days` × `--sessions-per-day`, minus review slots) can't fit the sum of topic weights, this **refuses loudly** with the minimum number of extra days needed — it never silently drops, compresses, or reorders a topic to make things fit.
5. Extra capacity beyond what the topics need automatically becomes review time — it never crashes or leaves dangling empty sessions.

## Run

```bash
python scripts/build_study_plan.py <topics.json> --days N [--sessions-per-day K] [--review-every M] [--output plan.md] [--json]
```

Start from `assets/topics_template.json`. `--review-every` must be ≥2 (a value of 1 would leave zero new-study slots). Output is a Markdown table + day-grouped checklist by default; `--json` prints the raw schedule instead.

## What this skill does NOT do

- Doesn't explain any topic, generate practice questions, or answer anything — pure scheduling, zero subject-matter content.
- Doesn't adapt the schedule based on how well a session actually went (no mastery tracking / spaced-repetition-by-performance) — it's a fixed, deterministic schedule computed up front, not an adaptive one. A future version could add a `--progress` input if this gap turns out to matter in real use.
- Doesn't call any LLM/AI API — pure stdlib arithmetic.
- Doesn't validate that the topic list itself is complete, correctly ordered, or exam-relevant — that judgment call stays with the student/teacher supplying the topic list.

## Verified

A 4-topic/14-day real schedule (correct spacing, no back-to-back repeats, sensible review distribution); an insufficient-capacity case correctly refused with an actionable "add N more days" message; an exact-fit case (10 days, weight sum = 8) verified to produce exactly 8 new + 2 review sessions; invalid `--review-every 1`, a duplicate topic name, and an out-of-range weight all correctly refused with exit code 2; a real bug (crash when a schedule has MORE capacity than topics need) was found and fixed during this testing.

## Known limitations (v0.1.0)

- Review-session topic selection is a simple round-robin, not a real spaced-repetition algorithm (e.g. no exponentially increasing review intervals per topic, no per-topic difficulty adjustment after review) — a deliberate v0.1.0 simplification, noted as a gap for a future version.
- No notion of session length/content within a session (a "session" is an opaque unit — the student decides how long an actual study block takes); doesn't account for topics needing meaningfully different amounts of time from each other beyond the coarse 1-5 weight.
- No real student elicitation source yet (see "Why this skill" above) — this skill's *scope choice* is grounded in thatlq1812's direct instruction to keep the Student tier deliberately simple and safe, not in a student survey. Treat future Student-tier skills the same way until a real survey exists.
