<!--
quality-eval report scaffold. Copy this file, fill every bracketed placeholder,
delete this comment block before finalizing. The registry entry is a summary of
this report, never a replacement for it — record observed behavior, not a
paraphrase of what the code appears to do.
-->

# quality-eval report: <skill_id> v<version>

**Evaluated on**: <YYYY-MM-DD>
**Evaluator**: <name/role of the accountable human or agent>
**Registry entry before this run**: `quality_score: null`

## Pass A — contract conformance under adversarial input

### A1. Extracted contract

Every behavioral claim copied verbatim from the target `SKILL.md` (description, compatibility, body, "does NOT do"). A claim too vague to test is recorded as `UNTESTABLE` here, not omitted.

| # | Claim (verbatim) | Where in SKILL.md |
| --- | --- | --- |
| 1 | <"..."> | <description / body §.. / limitations> |

### A2-A4. Result per claim

| # | Input used | Expected per SKILL.md | Observed (exit code + behavior) | Verdict |
| --- | --- | --- | --- | --- |
| 1 | <fixture file or hand-built input> | <what the claim promises> | <exit N, what actually happened> | <HOLDS / VIOLATED / UNTESTABLE> |

**Fixtures**: `python scripts/make_adversarial_fixtures.py --out <workdir>/fixtures`
**Hand-built fixtures for this skill**: <list them, and why the generator could not produce them>

### Pass A summary

- Claims checked: <N> — HOLDS <N> / VIOLATED <N> / UNTESTABLE <N>
- Untestable reasons: <state each; never round an untestable claim up to HOLDS>
- **Pass A verdict**: <PASS — no violated claim / FAIL — see violated claims above>

### Routed to stage 5 (not judged here)

<Anything this run surfaced that is a security question — harm outside declared scope — with a note that security-audit is a separate run. Empty is a valid answer.>

## Pass B — with-skill vs baseline

### Test prompts

| # | Prompt (as a real user would type it) | Type |
| --- | --- | --- |
| 1 | <concrete prompt with context> | typical |
| 2 | <harder-than-usual input> | edge |
| 3 | <near-miss: similar keywords, should route to a different skill> | near-miss |

### Assertions per test case

Written BEFORE running. Machine-checkable assertions get a script; state which.

| # | Assertion | Checked by |
| --- | --- | --- |
| 1 | <concrete, falsifiable outcome> | <script path / manual inspection> |

### Runs

| Harness | Test case | With-skill | Baseline | Notes |
| --- | --- | --- | --- | --- |
| <harness> | 1 | <pass/fail> | <pass/fail> | <what differed> |

### Deltas

| Harness | pass_rate(with-skill) | pass_rate(baseline) | delta |
| --- | --- | --- | --- |
| <harness> | <x.xx> | <x.xx> | <+/-x.xx> |

Record both absolute rates, not just the delta: a skill can pass 100% with-skill while the baseline also passes 100%, which means the skill changed nothing.

**Pass B verdict**: <PASS — positive delta on every tested harness / NEEDS-REVISION — which harness, which case, why>

## Combined verdict

**<pass / needs-revision>**

Both passes must clear. If `needs-revision`, the feedback below goes back to `skill-creator` — quality-eval never edits the skill itself.

### Feedback to skill-creator

<For each failure: the exact input, the behavior SKILL.md promises, the behavior observed. No "not good enough" without those three.>

## Registry entry to write

```json
"quality_score": {
  "contract_conformance": {
    "claims_checked": <N>,
    "holds": <N>,
    "violated": <N>,
    "untestable": <N>,
    "untestable_note": "<why>"
  },
  "harnesses_tested": ["<harness>", "<harness>"],
  "test_cases": <N>,
  "delta_pass_rate": { "<harness>": <x.xx> },
  "verdict": "<pass|needs-revision>",
  "date": "<YYYY-MM-DD>"
}
```

`quality_score != null` is necessary but not sufficient for "ready to use" — the skill also needs `security_audit.status = "passed"` from stage 5, run separately.
