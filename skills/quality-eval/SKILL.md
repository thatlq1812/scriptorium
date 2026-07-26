---
name: quality-eval
description: Scores an already-created skill's quality by running it for real on ≥2 verified harnesses, comparing with-skill vs baseline (no skill), against concrete pass/fail criteria per test case. Use after skill-creator finishes producing a skill, before the registry is allowed to mark that skill "ready to use." Do NOT evaluate security (that's security-audit, a separate step 5) — don't merge the two into one run.
license: MIT
compatibility: A process that runs on the target skill's actual harnesses — at minimum, the 2 harnesses already verified in that skill's `registry/skills.json` entry. Not yet applied for real to any Scriptorium skill (v0.1.0) — design complete, no real case run yet.
metadata:
  domain: meta
  task_type: review-qa
  risk_tier: N2
  pipeline_stage: 4
  source: self-authored
  elicited_from: "Grounded in SkillsBench (arXiv 2602.12670 — methodology: no-skill/curated/self-generated, deterministic verifiers, +16.2pp average but 16/84 tasks with negative delta). The baseline-comparison pattern (with-skill vs without-skill) adapted from github.com/anthropics/skills skill-creator (Apache-2.0, cleared via license-compliance-check), dropping the parts tied to Claude Code's own subagent/eval-viewer to stay harness-agnostic per the portability principle."
  version: 0.1.0
  adapted_from: "Baseline-comparison pattern from github.com/anthropics/skills skills/skill-creator (Apache-2.0), cleared 2026-07-26"
---

# quality-eval

Answers 1 question per skill: **does this skill genuinely improve results compared to not having it, on each harness it claims to be compatible with?** Doesn't grade "is the skill well-written" — grades by real task outcomes.

## Precondition

The skill being scored has already passed stage 3 (`skill-creator`), has a complete `SKILL.md` under `skills/<id>/`, and its registry entry has `quality_score: null`. If the skill doesn't exist yet, stop — this isn't the skill-creation step.

## Process

### 1. Write 2-3 real test prompts

Based on the skill's `description` (the "when to use" part), write prompts the way a real user would type them — concrete, with context, not abstract ("please use skill X" is a bad prompt; "I have a Q3 report file report.pdf, need it split into per-chapter parts to read separately" is a good prompt). Cover: 1 typical case + 1 edge case (harder-than-usual input) + 1 near-miss case if the skill is easily confused with another skill in the registry.

### 2. Run with-skill and baseline, on each declared-compatible harness

For each test prompt, on EVERY harness in that skill's `registry/skills.json.tags.harness_compatibility`:
- **With-skill**: the agent has access to the skill, performs the task.
- **Baseline**: same agent/model, same prompt, WITHOUT the skill — performs the task using its existing capabilities.

At least 2 harnesses (per the requirement in `docs/specs/STRATEGY_SPEC.md` §3 step 4). If the skill has only 1 harness verified so far, quality-eval can't run fully — report that, don't unilaterally relax it to 1 harness.

### 3. Grade each run against concrete criteria, not gut feeling

Before running, write a concrete assertion for each test case (e.g. "the output file has the correct field X in index.json," "no step where the agent invents a command that doesn't exist"). If an assertion is machine-checkable, write a script to check it — don't eyeball and judge; scripted checks are faster and more consistent across runs.

### 4. Compute delta, not just absolute pass/fail

For each harness: `pass_rate(with_skill) - pass_rate(baseline)`. Record both numbers, not just the delta — a skill might "pass 100% with-skill" but the baseline also passes 100% (the skill made no difference, a sign the skill is redundant or its description is mis-targeted).

### 5. Verdict

- Positive delta on EVERY tested harness → `verdict: "pass"`.
- Delta ≤ 0 on any harness → `verdict: "needs-revision"`, hand back to `skill-creator` with concrete feedback (don't just say "not good enough" — state exactly which test case failed and why), never fix SKILL.md inside quality-eval.
- SkillsBench shows even curated skills have ~19% of tasks with negative delta — a "needs-revision" verdict is a normal outcome of the process, not a failure of quality-eval.

### 6. Record the result in the registry

```json
"quality_score": {
  "harnesses_tested": ["claude-code", "..."],
  "test_cases": 3,
  "delta_pass_rate": { "claude-code": 0.67, "...": 0.33 },
  "verdict": "pass",
  "date": "YYYY-MM-DD"
}
```

`quality_score != null` is a NECESSARY (not sufficient) condition for a skill to be "ready to use" — it also needs `security_audit.status = "passed"` (step 5).

## What quality-eval does NOT do

- Doesn't evaluate security/injection — that's `security-audit`, step 5, run separately.
- Doesn't fix SKILL.md itself when the verdict is "needs-revision" — hands it back to `skill-creator`.
- Doesn't add a harness to `tags.harness_compatibility` just because it was tested there — harness compatibility is set when a skill *runs*, quality_score measures *how well* it runs — two different things.
