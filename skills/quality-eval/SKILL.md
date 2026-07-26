---
name: quality-eval
description: Scores an already-created skill's quality in two passes — first checking that every behavioral guarantee its own SKILL.md states still holds under adversarial input, then comparing with-skill vs baseline (no skill) for real on ≥2 verified harnesses, against concrete pass/fail criteria. Use after skill-creator finishes producing a skill, before the registry is allowed to mark that skill "ready to use." Do NOT evaluate security (that's security-audit, a separate step 5) — don't merge the two into one run.
license: MIT
compatibility: A process that runs on the target skill's actual harnesses — at minimum, the 2 harnesses already verified in that skill's `registry/skills.json` entry. Pass A additionally needs Python 3.11+ (stdlib only) to generate the bundled fixtures. Not yet applied for real to any Scriptorium skill (v0.2.0) — design complete, no real evaluation run yet; running stage 4 stays deliberately deferred by owner decision (2026-07-26).
metadata:
  domain: meta
  task_type: review-qa
  risk_tier: N2
  pipeline_stage: 4
  source: self-authored
  elicited_from: "Grounded in SkillsBench (arXiv 2602.12670 — methodology: no-skill/curated/self-generated, deterministic verifiers, +16.2pp average but 16/84 tasks with negative delta). The baseline-comparison pattern (with-skill vs without-skill) adapted from github.com/anthropics/skills skill-creator (Apache-2.0, cleared via license-compliance-check), dropping the parts tied to Claude Code's own subagent/eval-viewer to stay harness-agnostic per the portability principle. Pass A (contract conformance under adversarial input) was elicited from a real event in this project, not from literature: the 2026-07-26 hardening round found 17 reproducible defects across the 5 freshly-authored harvested skills in roughly 20 minutes of hostile-input testing, 3 of which falsified the skill's own headline guarantee — see docs/STATUS.md 'v0.2.0 hardening round' for the full record and references/adversarial-input-catalog.md for the input classes distilled from it."
  version: 0.2.0
  adapted_from: "Baseline-comparison pattern from github.com/anthropics/skills skills/skill-creator (Apache-2.0), cleared 2026-07-26"
  changelog_0_2_0: "Added Pass A (contract conformance under adversarial input) ahead of the existing baseline-delta comparison, now Pass B, after the 2026-07-26 hardening round showed the failure mode this stage most needs to catch is not 'the skill does not help' but 'the skill's documented guarantee is false in exactly the case the guarantee exists for' — a class that a with-skill/baseline delta on happy-path prompts cannot detect. Added 3 supporting files (adversarial-input catalog, fixture generator, evaluation report template) so the stage stops being pure prose. The security boundary is restated explicitly: Pass A asks whether documented behavior is true, stage 5 asks whether behavior can cause harm outside declared scope — same inputs sometimes, two separate runs always."
---

# quality-eval

Answers 2 questions per skill, in this order:

- **Pass A — is what the skill says about itself true?** Every behavioral guarantee written in its `SKILL.md`, checked against the input most likely to break it.
- **Pass B — does the skill genuinely improve results compared to not having it?** On each harness it claims to be compatible with.

Doesn't grade "is the skill well-written" — grades by real behavior and real task outcomes.

Pass A comes first because it is cheaper and because a skill that fails it cannot be rescued by a good Pass B score: a skill whose documented guarantee is false actively misleads the next agent that reads it, which is worse than having no skill at all.

## Precondition

The skill being scored has already passed stage 3 (`skill-creator`), has a complete `SKILL.md` under `skills/<id>/`, and its registry entry has `quality_score: null`. If the skill doesn't exist yet, stop — this isn't the skill-creation step.

## Pass A — contract conformance under adversarial input

### A1. Extract the contract

Read the target `SKILL.md` and copy out every sentence that asserts behavior, verbatim, as a numbered checklist. These are claims like "fails loudly instead of inventing metadata," "never prints raw cell values," "refuses a path outside `--root`," "deduplicates by DOI or normalized title," "refuses to run unless the intake passes." Include claims made in `description`, `compatibility`, the body, and the "does NOT do" section — a promise in any of them is still a promise.

Anything vague enough that you cannot write a pass/fail test for it is itself a finding: record it as `UNTESTABLE — claim not falsifiable as written` and hand that back to `skill-creator`. A guarantee nobody can check is not a guarantee.

### A2. Build the input where each claim is most likely to break

For each claim, construct the input a careless-but-plausible user would produce that sits exactly on the claim's edge — not the happy path the author already tried. `references/adversarial-input-catalog.md` lists the 9 input classes distilled from the 2026-07-26 hardening round, with which claim shape each one probes.

```bash
python scripts/make_adversarial_fixtures.py --out <workdir>/fixtures
```

Generates the reusable file-shaped fixtures (encoding, structure, numeric edge, nesting, malformed, delimiter/markup injection, embedded instructions, unfilled template, sparse keys) plus a `MANIFEST.md` mapping each file to the claim it probes. Skill-specific fixtures — an identifier that does not resolve, a record that violates the skill's own invariant — are written by hand for that skill; the generator does not invent domain semantics.

### A3. Run for real and record what happened

Run the skill's own documented commands against each fixture. Record exit code, stderr, and the output artifact — not a summary of them. Never mark a claim as holding because the code "looks like" it handles the case; the hardening round found defects in code that read correctly.

### A4. Verdict per claim

- **HOLDS** — the observed behavior matches the claim.
- **VIOLATED** — the claim is false for this input. Record the exact input, the expected behavior per SKILL.md, and the observed behavior.
- **UNTESTABLE** — could not be exercised in this environment (state why, e.g. symlink creation needing admin rights). Never round this up to HOLDS.

**Any VIOLATED claim fails Pass A**, regardless of how strong the Pass B delta is, and regardless of how narrow the input looks. A crash, a silent placeholder output, or a gate that lets unfilled input through is a violated contract even when the happy path works perfectly.

### A5. Boundary against stage 5 — do not merge

Pass A asks *"is the documented behavior true?"*. `security-audit` (stage 5) asks *"can this behavior cause harm outside its declared scope?"*. The two use overlapping inputs and stay two separate runs (`docs/specs/STRATEGY_SPEC.md` §7 point 2).

- A tool that crashes on a hostile file → Pass A finding (it claimed to refuse cleanly).
- A tool that reads a file outside its declared root → stage 5 finding (harm outside declared scope).
- A tool that echoes an instruction-shaped cell value back into agent-visible output → Pass A if it claimed never to print raw values; stage 5 decides whether that is exploitable.

If a Pass A run surfaces something in stage 5's territory, note it and route it there — do not expand this run into a security audit.

## Pass B — does the skill beat no skill

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

## Combined verdict

Both passes must clear:

- Pass A: no `VIOLATED` claim. Pass B: positive delta on EVERY tested harness → `verdict: "pass"`.
- Any `VIOLATED` claim, or delta ≤ 0 on any harness → `verdict: "needs-revision"`, hand back to `skill-creator` with concrete feedback (don't just say "not good enough" — state the exact input, the claimed behavior, and the observed behavior), never fix SKILL.md inside quality-eval.
- SkillsBench shows even curated skills have ~19% of tasks with negative delta — a "needs-revision" verdict is a normal outcome of the process, not a failure of quality-eval.

Fill `assets/eval_report_template.md` as the run's deliverable; the registry entry below is the summary of it, not a replacement for it.

## Record the result in the registry

```json
"quality_score": {
  "contract_conformance": {
    "claims_checked": 12,
    "holds": 11,
    "violated": 0,
    "untestable": 1,
    "untestable_note": "symlink rejection: creating a symlink needs admin rights unavailable in this environment"
  },
  "harnesses_tested": ["claude-code", "..."],
  "test_cases": 3,
  "delta_pass_rate": { "claude-code": 0.67, "...": 0.33 },
  "verdict": "pass",
  "date": "YYYY-MM-DD"
}
```

`quality_score != null` is a NECESSARY (not sufficient) condition for a skill to be "ready to use" — it also needs `security_audit.status = "passed"` (step 5).

## Bundled files

- `references/adversarial-input-catalog.md` — the 9 input classes, each with the claim shape it probes and the real defect it caught on 2026-07-26.
- `scripts/make_adversarial_fixtures.py` — writes the reusable file fixtures + a manifest into a directory you name. Stdlib only, local, no network.
- `assets/eval_report_template.md` — the report scaffold for a full Pass A + Pass B run.

## What quality-eval does NOT do

- Doesn't evaluate security/injection — that's `security-audit`, step 5, run separately (see A5).
- Doesn't fix SKILL.md itself when the verdict is "needs-revision" — hands it back to `skill-creator`.
- Doesn't add a harness to `tags.harness_compatibility` just because it was tested there — harness compatibility is set when a skill *runs*, quality_score measures *how well* it runs — two different things.
- Doesn't prove a skill is correct. Pass A proves specific claims false; it never proves the remainder true. A clean Pass A means "no documented guarantee was falsified by the inputs we tried," nothing stronger.
- Doesn't call any LLM/AI API of its own — every judgment here is made by the evaluating agent/human on its own backend, per `docs/specs/STRATEGY_SPEC.md` §2.

## Known limitations (v0.2.0)

- Pass A's coverage is bounded by the claim list you extract and the fixtures you build. A guarantee the SKILL.md never states cannot be checked here — which is a reason to prefer skills that state their guarantees explicitly.
- The fixture generator produces file-shaped inputs only. Skills whose input is a prompt, an API response, or another skill's output need hand-built fixtures; the catalog describes the shapes, the script cannot generate them.
- Pass B still requires ≥2 verified harnesses and therefore cannot run at all for a skill verified on one harness so far — unchanged from v0.1.0, and not something Pass A relaxes.
- Never applied end-to-end to a real skill. The process is grounded in a real hardening round, but the round was run ad hoc, before this stage existed — the first real run will likely expose gaps in the checklist itself.
