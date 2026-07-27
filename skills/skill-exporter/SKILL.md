---
name: skill-exporter
description: Packages one or more skills from this repo into a single .zip for someone outside this project — a colleague, a friend, another project — to drop into their own agent. Use when a user says something like "prepare a skill pack for me/a friend for [purpose/workflow]" — the calling agent interviews the user (free-form, no fixed script; a suggested checklist is below) to figure out who it's for and what they need, maps that to registry tags, then runs the 2 bundled scripts to list candidates and export. Do NOT export a skill with license_debt set or a security_audit status other than "passed" — both scripts hard-refuse this, no override flag exists.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse, zipfile, shutil) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-27). See "Verified" section below for real test-case detail.
metadata:
  domain: meta
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (2026-07-27): after discussing skill-importer (judged unnecessary — scout-harvester + license-compliance-check + skill-creator already form the import pipeline, a separate importer would duplicate it) and skill-exporter (judged genuinely new — Scriptorium had a create/audit/catalog side but no distribution side yet, this is the missing piece). Owner's framing: the trigger is a free-form user prompt ('chuẩn bị pack skill cho tôi/bạn tôi cho việc X'), the interview approach is 'tuỳ trí tuệ của agent làm việc' (up to whichever agent runs it) — not a fixed script this skill can dictate — but 'có chuẩn vẫn hơn không' (a suggested standard is still better than none). Owner explicitly declined a quality_score caveat in the exported output ('tôi kiểm soát được nó') — this skill does not editorialize about quality_score; the hard license_debt/security_audit exclusion is kept regardless, since that is a distinct written registry rule (registry/SCHEMA.md), not a quality judgment call."
  version: 0.1.0
  grounding: not_applicable
  object_type: []
---

# skill-exporter

Packages skills for someone outside this repo. The distribution half of the pipeline — everything else in Scriptorium creates/audits/catalogs skills; this is the only skill whose job is to hand a finished bundle to somebody else.

## Suggested intake (not a fixed script — the calling agent's own judgment drives this)

There is no mandated question sequence — the owner was explicit that this depends on the calling agent's own intelligence, not something this skill can script. A reasonable starting checklist, useful as a baseline rather than a requirement:

1. **Who is this for?** (the user themselves, a colleague, a friend, another project) — informs tone/scope, not a registry filter by itself.
2. **What task/workflow?** — map to `task_type` (`research`/`document-conversion`/`drafting`/`review-qa`/`coordination`) and, if it's clearly domain-specific (legal, education...), to `domain`.
3. **Any specific skills already known/wanted by name?** — pass directly to `export_bundle.py`, skip the filtering step.
4. **Anything explicitly out of scope?** — narrow with `--object-type` or just hand-pick from the candidate list rather than exporting everything that matched.

## List candidates

```bash
python skills/skill-exporter/scripts/list_candidates.py --domain legal --task-type review-qa [-o candidates.json]
```

Filters are OR-within-axis (`--domain legal general` matches either), AND-across-axis. Always hard-excludes any skill with `license_debt` set or `security_audit.status != "passed"` — printed separately to stderr, never silently dropped without explanation.

## Export a bundle

```bash
python skills/skill-exporter/scripts/export_bundle.py <skill_id> [<skill_id> ...] -o bundle.zip --for "short description of who/what this is for" [--force]
```

Auto-resolves dependencies recursively: if a requested skill's registry `dependencies` field names another skill_id (not a package pin), that skill is pulled in too, and so on. A `MANIFEST.md` at the zip root lists every included skill (with real version/tags/security_audit status) and separately lists any non-skill dependency (e.g. a PyPI package pin, or `uv`) the recipient still needs to install themselves — the bundle does not vendor those.

Exit 0 = exported. Exit 1 = a requested skill_id doesn't exist, or fails the hard-exclusion rule (whole export refused, nothing written — not a partial bundle with the bad skill quietly dropped). Exit 2 = malformed registry, or output path already exists without `--force`.

## What this skill does NOT do

- Does not interview the user itself — that's the calling agent's job, using its own language capability (same division of labor as `deep-research`/`legal-web-search`).
- Does not call any LLM/AI API — Scriptorium never does; both scripts are stdlib-only, zero network.
- Does not editorialize about `quality_score` (owner decision, 2026-07-27) — the field is shown factually in `list_candidates.py`'s output like any other registry field, not flagged as a blocking caveat.
- Does not override the license_debt/security_audit hard exclusion for any reason — no `--force`-style flag exists for this specific check (unlike the unrelated output-overwrite `--force`).
- Does not vendor non-skill dependencies (Python packages, external tools) into the bundle — only lists them in `MANIFEST.md` for the recipient to install via their own `python-env-bootstrap`-equivalent.

## Verified

list_candidates.py filtered by domain/task_type/object_type against the real registry (37 skills), correctly excluding any skill with license_debt or a non-passed security_audit (verified directly, none currently in the ledger to exercise against for real, so tested via direct function calls with synthetic data). export_bundle.py verified real end-to-end: exporting legal-citation-checker correctly auto-resolved its dependency chain 2 levels deep (document-ai-structurer → python-env-bootstrap), produced a real .zip with all 3 skill folders + a MANIFEST.md separating skill dependencies (bundled) from non-skill dependencies like docling/uv (listed, not bundled); overwrite-protection and unknown-skill_id refusal both correct.

## Known limitations (v0.1.0, not yet through official quality-eval)

- No skill in the registry currently has `license_debt` set or a non-`passed` `security_audit.status` (the debt ledger is empty as of this session) — the hard-exclusion path was verified via direct function calls with synthetic data, not a real registry entry. Re-verify against a real excluded entry if/when one exists.
- Dependency resolution only follows the `dependencies` field's exact string match against `skill_id` — a dependency declared with a typo or version-qualified id (unlike this registry's convention) would be silently treated as a non-skill dependency instead of pulled in.
- No de-duplication warning if the same skill is reachable via 2 different requested skills' dependency chains — harmless (the zip write is idempotent per path within one run), just not flagged.
- Hasn't passed stage 4 (quality eval, ≥2 harnesses) or stage 5 (security audit — self-audited only this session: stdlib-only, no eval/exec/subprocess/os.system/network calls found).
