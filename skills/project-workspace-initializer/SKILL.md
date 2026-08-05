---
name: project-workspace-initializer
description: Generic engine, two layers, for ANY profession/workflow from a caller-supplied JSON template -- the mechanism itself knows nothing about any specific profession. `init_workspace.py` runs ONCE to set up a workspace root's own top-level structure (workspace-declared subdirs, a local copy of the template under `projects/_templates/<template_id>/`, and a `WORKSPACE.md` control panel). `scaffold_workspace.py` runs PER new matter/project to create a date-indexed `projects/project_YYYYMMDD_NN/` directory with the template's project-declared subdirectories (e.g. `source/`, `work/`, `draft/`, `deliverables/`, `archives/`) plus a generated `PROJECT.md` control-panel file, auto-incrementing the day's sequence number by scanning existing project directories (never guesses, never overwrites). Both control-panel files exist so a non-tech user can drive the calling agent through a multi-step task without navigating the directory tree manually. `assets/templates/legal-practitioner/template.json` is the only bundled template right now -- because it's the only profession with a real pilot behind it (see "Why this skill" below), not because the mechanism is legal-specific. Use `init_workspace.py` once per new workspace, then `scaffold_workspace.py` for each new real-world matter/project spanning multiple work sessions. Do NOT use this for a one-off single-file task.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, re, shutil, datetime, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29, init_workspace.py added and verified 2026-08-05).'
metadata:
  domain: general
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in a real non-tech-user pilot (a legal-practitioner workspace deployment, recorded in docs/ROADMAP.md's 'New planned roadmap items' 2026-07-29 entry -- the pilot deployment itself is no longer directly accessible on this machine, so the already-recorded workflow description in ROADMAP.md is treated as the elicitation record, same discipline as any other written elicitation source in this registry). Directory-scaffolding mechanism lightly cross-checked against public conventions (cookiecutter's template+variables pattern) via a web survey, not cloned -- kept stdlib-only, no templating-engine dependency, since the actual need (fixed subdirectory set + a prompts file) doesn't require one. Only one real profession template exists so far (legal-practitioner, the actually-piloted one) -- no template invented for a profession with no real pilot. `init_workspace.py`/workspace_subdirs+workspace_md_prompts (2026-08-05) are grounded in the same ROADMAP.md record's own description of the pilot's `d:/my-workspace` deployment (`projects/` root + `projects/_templates/` template location) -- a structural detail of the same already-recorded pilot, not a new elicitation."
  version: 0.2.1
  changelog_0_2_1: "WORKSPACE.md now includes a fixed 'Shared resources (once per workspace, never per project)' section (skills install location + Python venv) -- owner reported real friction from a sibling project's worker.py re-linking a fresh .agents/skills junction into every new small project instead of once per workspace, the same anti-pattern as a per-project venv. Not template-declared content (workspace_md_prompts stays template-specific) since this is a fact about the skill mechanism itself, not a profession-specific workflow step. Matching section added to skill-exporter's MANIFEST.md (see that skill's own changelog)."
  changelog_0_2_0: "Added init_workspace.py: a real workspace-level init step, distinct from scaffold_workspace.py's per-project init -- previously the registry's security_audit note referenced a nonexistent 'init_root_workspace.py' (confirmed via git log --all: never existed in this repo, a stale/fabricated note) while this skill only actually did project-level scaffolding. Built for real per owner direction (2026-08-05) instead of leaving the registry note uncorrected: template.json gained workspace_subdirs + workspace_md_prompts (legal-practitioner populated with real content grounded in the same ROADMAP.md pilot record). Registry version was also out of sync with this file (registry said 0.2.0, this file said 0.1.0) before this fix -- now reconciled."
  changelog_0_1_1: "Reworded the frontmatter description to lead with the generic template-driven mechanism instead of the legal-practitioner template -- the mechanism was already profession-agnostic (any template.json), but the description read as legal-specific since it opened with the bundled template's path. No functional change. Owner-directed (2026-08-05)."
  grounding: not_applicable
  object_type: ["workspace"]
---

# project-workspace-initializer

A scaffolder, not a project-management tool: creates the directory structure and a starting `PROJECT.md`, then gets out of the way. No tracking, no state beyond the filesystem itself.

## Why this skill, and why this scope

A real non-tech user (a legal practitioner, piloted directly) working with an agent across a multi-session matter kept losing track of which files were source material, which were in-progress drafts, and which were final deliverables -- and re-explaining the workflow to the agent at the start of every session. The fix isn't a database or a UI, it's the same idea `legal-form-filler`/`personal-profile-manager` already use for other problems: a generic engine (the scaffolder) driven by caller-supplied specifics (the profession template), so the mechanism doesn't need to know anything about any specific profession, and a new profession template can be added without touching the script.

Only the legal-practitioner template exists right now, because that's the only profession with a real pilot behind it -- adding a template for a profession with no real workflow behind it would be inventing process, the same thing `legal-form-filler` explicitly declined to do for "which form applies to a procedure."

## Run

### 1. Initialize the workspace (once per workspace)

```bash
python scripts/init_workspace.py <template.json> <workspace_root> [--force]
```

Start from `assets/templates/legal-practitioner/template.json`. Creates `workspace_root` (if missing), each of the template's `workspace_subdirs` under it, a local copy of the template itself under `workspace_root/projects/_templates/<template_id>/` (so later `scaffold_workspace.py` runs don't need to reference this repo's path), and a `WORKSPACE.md` control-panel file rendering the template's `workspace_md_prompts`. Refuses (exit 1) if `WORKSPACE.md` or the template-copy destination already exists, unless `--force`.

### 2. Scaffold a new project (once per matter/project)

```bash
python scripts/scaffold_workspace.py <template.json> <projects_root> [--date YYYY-MM-DD]
```

Point `<template.json>` at the workspace's own local copy (`workspace_root/projects/_templates/<template_id>/template.json`, printed by `init_workspace.py`) once the workspace is initialized. `projects_root` is the parent directory under which `project_YYYYMMDD_NN/` gets created (`workspace_root/projects/`, per `init_workspace.py`'s convention). The sequence number `NN` is derived by scanning `projects_root` for existing `project_<same-date>_NN` directories and taking `max+1` -- if none exist yet for that date, starts at `01`. `--date` overrides today's date (useful for scripted testing or backfilling); omit it in normal use.

Output: the new project directory with the template's declared project-level subdirectories (defaults to `source/`, `work/`, `draft/`, `deliverables/`, `archives/` in the legal-practitioner template, but a template can declare any subdirectory list) plus a `PROJECT.md` rendering each of the template's `project_md_prompts` as a heading + instruction block.

### Template schema

```json
{
  "template_id": "string, matches the folder name under assets/templates/",
  "label": "human-readable label, used in WORKSPACE.md/PROJECT.md's title",
  "workspace_subdirs": ["projects", "projects/_templates"],
  "workspace_md_prompts": [
    {"heading": "string", "text": "string, the pre-formulated instruction for this workspace-level step"}
  ],
  "subdirs": ["source", "work", "draft", "deliverables", "archives"],
  "project_md_prompts": [
    {"heading": "string", "text": "string, the pre-formulated instruction for this step"}
  ]
}
```

`init_workspace.py` only reads `template_id`/`label`/`workspace_subdirs`/`workspace_md_prompts`; `scaffold_workspace.py` only reads `template_id`/`label`/`subdirs`/`project_md_prompts` -- a template must declare all 6 keys, since both scripts validate independently and neither guesses a default for a missing key.

## What this skill does NOT do

- Does not track project state (which step is done, what's overdue) -- `PROJECT.md`/`WORKSPACE.md` are static starting points, not a live dashboard. A user editing them afterward is expected and fine.
- Does not invent a template for a profession with no real elicitation source -- see "Why this skill" above. Adding a new template requires the same discipline as adding a new niche-specializer skill (`CLAUDE.md` principle 4): a real practitioner workflow, not a guess.
- Does not move or reorganize files after scaffolding -- purely a one-time directory+file creation step.
- Does not re-render `WORKSPACE.md`/`PROJECT.md` if the template changes after init/scaffold -- both are one-time snapshots.
- Does not call any LLM/AI API.

## Verified

Scaffolded a real workspace from `assets/templates/legal-practitioner/template.json` into a fresh `projects_root`: correct `project_YYYYMMDD_01` directory name (today's date), all 5 subdirectories created, `PROJECT.md` rendered with all 5 prompts in order with correct headings. Ran a second scaffold against the same `projects_root`/date immediately after: correctly produced `..._02`, no collision, first project's directory untouched. Ran with `--date 2020-01-01` twice: correctly produced `..._01` then `..._02` for that historical date, independent of today's-date sequence. Malformed template (missing `project_md_prompts` key) correctly refused (exit 2, naming the missing key); a `project_md_prompts` entry missing `text` correctly refused (exit 2, naming the index); nonexistent template path correctly refused (exit 2).

**v0.2.0 (2026-08-05), `init_workspace.py`**: initialized a fresh workspace root from the real `legal-practitioner` template -- `projects/` and `projects/_templates/` created, template copied to `projects/_templates/legal-practitioner/template.json`, `WORKSPACE.md` rendered with all 3 real `workspace_md_prompts` and the correct `scaffold_workspace.py` invocation line pointing at the local template copy. Ran `scaffold_workspace.py` against that local copy immediately after -- produced a correct `project_20260805_01/` with all 5 subdirs and `PROJECT.md`, confirming the two scripts chain end-to-end. Re-ran `init_workspace.py` on the same workspace without `--force` -- correctly refused (exit 1, named `WORKSPACE.md` already exists). Re-ran with `--force` -- correctly re-initialized (exit 0). A template missing `workspace_md_prompts` correctly refused (exit 2, naming the missing key).

**v0.2.1 (2026-08-05)**: re-ran `init_workspace.py` and confirmed the real generated `WORKSPACE.md` contains the "Shared resources (once per workspace, never per project)" section verbatim, positioned between "Starting a new project" and "Prompts" as intended, with the rest of the file (subdirs, prompts) unaffected.

## Known limitations (v0.2.0)

- Sequence-number scanning only looks at direct children of `projects_root` matching the exact `project_YYYYMMDD_NN` pattern -- a differently-named existing directory for the same conceptual project is invisible to it (by design: never guess an existing project is "the same one").
- No re-render path if a template's prompts change after a workspace/project was already initialized/scaffolded -- `WORKSPACE.md`/`PROJECT.md` are one-time snapshots, not regenerated automatically.
- `init_workspace.py`'s re-init detection only checks for `WORKSPACE.md` and the template-copy directory -- a workspace manually stripped of one but not the other is a state this script hasn't been tested against.
- Only one real profession template (`legal-practitioner`) exists; adding more is the next open step once a real pilot exists for another profession (see `UPGRADE_PLAN_20260729.md` Item 2).
