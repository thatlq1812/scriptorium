---
name: dedup-novelty-check
description: Checks whether a candidate skill significantly overlaps an existing skill in the registry, using a script that scores overlap on domain/task_type/description — not eyeballed guessing. Use right before starting skill-creator for a new skill. Do NOT use to evaluate quality or license (that's quality-eval and license-compliance-check).
license: MIT
compatibility: 'Pure Python 3 stdlib script (argparse/json/re), no dependency to install, no venv needed. Verified running clean: Claude Code, Windows (2026-07-26, tested both a flagged case and a safe case against the real registry).'
metadata:
  domain: meta
  task_type: review-qa
  risk_tier: N1
  pipeline_stage: 8
  source: self-authored
  elicited_from: "Distilled from the rule already recorded in registry/SCHEMA.md ('Dedup/novelty-check principle', pipeline step 9 in STRATEGY_SPEC) — this step was previously a manual rule, formalized into a real overlap-scoring script, verified against the registry's 8 existing skills at the time"
  version: 0.1.0
---

# dedup-novelty-check

Answers: **does an existing skill in the registry already cover ≥80% of this candidate's scope?** Measured by a number, not a "this sounds familiar" feeling.

## How overlap is computed

`scripts/check_dedup.py` — pure Python standard library, no dependency:

```bash
python scripts/check_dedup.py \
  --domain <domain1> <domain2>... \
  --task-type <task_type1>... \
  --description "short candidate description (Vietnamese or English both work)"
```

Formula: `combined_score = 0.4 × domain_jaccard + 0.4 × task_type_jaccard + 0.2 × description_token_jaccard`, compared against every skill in `registry/skills.json`. Weight leans toward tags (domain/task_type) since that's a structured signal, more trustworthy than raw vocabulary overlap in `elicited_from`.

Default threshold `0.8` (matches the "≥80% scope" rule set in `registry/SCHEMA.md`) — adjust via `--threshold` if a specific case needs it more sensitive/looser.

## Process

1. Run the script with the NEW candidate's expected domain/task_type/description (before writing the real SKILL.md).
2. Exit code `1` + a FLAGGED list → a significantly overlapping skill exists. Prefer extending/versioning that skill (bump `version`, add capability) over creating a parallel skill — unless there's a clear reason to split it out (record that reason in the new skill's `elicited_from`).
3. Exit code `0` → safe, hand off to `skill-creator`.

## Known limitations (v0.1.0)

- `description_token_jaccard` only compares raw tokens (no stemming, no synonym handling) — two descriptions with the same meaning but completely different vocabulary will score artificially low. The low 0.2 weight here is deliberate, not meant to be the primary signal.
- Can't detect overlap in *implementation approach* when domain/task_type/description differ but the internal logic is identical — only catches overlap at the declared (registry) layer, doesn't read the content of other skills' `SKILL.md`.
