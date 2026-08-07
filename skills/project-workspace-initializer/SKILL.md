---
name: project-workspace-initializer
description: Generic engine, three modes, for ANY profession/workflow from a caller-supplied JSON template -- knows nothing about any specific profession. `init_workspace.py` runs ONCE per workspace (subdirs, local template copy, `WORKSPACE.md` panel). `scaffold_workspace.py` runs PER new matter inside a workspace, creating a date-indexed `project_YYYYMMDD_NN/` dir plus `PROJECT.md`, auto-incrementing the sequence (never guesses, never overwrites). `init_project.py` scaffolds ONE standalone project at a caller-given path -- same subdirs/`PROJECT.md`, no workspace wrapper, no date naming, for when one project is the whole unit of work. Panel files let a non-tech user drive the agent without navigating the tree manually. Several profession templates are bundled under `assets/templates/` -- pick the closest match, or supply your own. Use `init_workspace.py` + `scaffold_workspace.py` for many matters over time; use `init_project.py` for one standalone project. Do NOT use for a one-off single-file task.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, re, shutil, datetime, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29, init_workspace.py added and verified 2026-08-05, init_project.py + 4 new templates added and verified 2026-08-07).'
metadata:
  domain: general
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in a real non-tech-user pilot (a legal-practitioner workspace deployment, recorded in docs/ROADMAP.md's 'New planned roadmap items' 2026-07-29 entry -- the pilot deployment itself is no longer directly accessible on this machine, so the already-recorded workflow description in ROADMAP.md is treated as the elicitation record, same discipline as any other written elicitation source in this registry). Directory-scaffolding mechanism lightly cross-checked against public conventions (cookiecutter's template+variables pattern) via a web survey, not cloned -- kept stdlib-only, no templating-engine dependency, since the actual need (fixed subdirectory set + a prompts file) doesn't require one. `init_workspace.py`/workspace_subdirs+workspace_md_prompts (2026-08-05) are grounded in the same ROADMAP.md record's own description of the pilot's `d:/my-workspace` deployment (`projects/` root + `projects/_templates/` template location) -- a structural detail of the same already-recorded pilot, not a new elicitation. v0.3.0 (2026-08-07): 4 additional templates (media-content-creator, educator, brand-design-project, researcher-writer) are grounded differently -- not an outside practitioner pilot, but this registry's own already-built and already-verified skill clusters (each `project_md_prompts` step names the real skill(s) for that step, in the order that skill cluster's own SKILL.md files already document them chaining, cross-checked directly against registry/skills.json before writing). Owner explicitly authorized this lower/different grounding bar for template.json content specifically (2026-08-07, recorded in docs/DECISIONS_PENDING.md), distinct from the niche-specializer elicitation bar the skill mechanism itself and legal-practitioner still follow."
  version: 0.3.1
  changelog_0_3_1: "Doc-only (2026-08-07): repointed media-content-creator/brand-design-project template references from poster-generator/svg-poster-builder to html-poster-composer (both superseded same date, registry operational_status). No script change."
  changelog_0_3_0: "Owner-directed (2026-08-07): added init_project.py (standalone single-project scaffold, no workspace wrapper/date-indexing) and 4 new templates (media-content-creator, educator, brand-design-project, researcher-writer), each mapped to an already-built, already-verified skill cluster in this registry rather than a new outside practitioner pilot -- owner explicitly waived the per-template real-practitioner-elicitation bar for these (\"template hoàn toàn có thể điều chỉnh được... cá nhân bạn cũng đủ năng lực để biết cluster nào thì sẽ khai báo project thế nào\"), reasoning that a PROJECT.md/template.json is a reconfigurable ticket, not a fixed process commitment. legal-practitioner remains the one directly-piloted-user-grounded template. All 5 templates re-verified end-to-end through all 3 scripts (init_workspace.py, scaffold_workspace.py, init_project.py)."
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

`legal-practitioner` is the only template grounded in a directly-piloted real user; it stays the highest-confidence reference. The other 4 bundled templates (v0.3.0) are a deliberately different, lighter-weight kind of grounding: each maps directly onto an already-built, already-verified skill cluster in this registry (see `elicited_from` below and "Bundled templates") rather than an outside practitioner's workflow -- owner-authorized 2026-08-07 on the reasoning that a `PROJECT.md`/`template.json` is a reconfigurable ticket/checklist, not a fixed process commitment, and the registry's own documented skill-chain order is itself a legitimate, directly-verifiable source. Adding a template for a workflow this registry has no real skill cluster for would still be inventing process -- that bar is unchanged.

## Run

### 1. Initialize the workspace (once per workspace, multi-project mode)

```bash
python scripts/init_workspace.py <template.json> <workspace_root> [--force]
```

Creates `workspace_root` (if missing), each of the template's `workspace_subdirs` under it, a local copy of the template itself under `workspace_root/projects/_templates/<template_id>/` (so later `scaffold_workspace.py` runs don't need to reference this repo's path), and a `WORKSPACE.md` control-panel file rendering the template's `workspace_md_prompts`. Refuses (exit 1) if `WORKSPACE.md` or the template-copy destination already exists, unless `--force`.

### 2. Scaffold a new project (once per matter/project, inside a workspace)

```bash
python scripts/scaffold_workspace.py <template.json> <projects_root> [--date YYYY-MM-DD]
```

Point `<template.json>` at the workspace's own local copy (`workspace_root/projects/_templates/<template_id>/template.json`, printed by `init_workspace.py`) once the workspace is initialized. `projects_root` is the parent directory under which `project_YYYYMMDD_NN/` gets created (`workspace_root/projects/`, per `init_workspace.py`'s convention). The sequence number `NN` is derived by scanning `projects_root` for existing `project_<same-date>_NN` directories and taking `max+1` -- if none exist yet for that date, starts at `01`. `--date` overrides today's date (useful for scripted testing or backfilling); omit it in normal use.

Output: the new project directory with the template's declared project-level subdirectories plus a `PROJECT.md` rendering each of the template's `project_md_prompts` as a heading + instruction block.

### 3. Scaffold ONE standalone project (v0.3.0, no workspace)

```bash
python scripts/init_project.py <template.json> <project_dir> [--force]
```

For when a single project is the whole unit of work -- no `projects/` root, no `WORKSPACE.md`, no `_templates/` copy, no date/sequence naming. Creates the template's `subdirs` directly under `project_dir` and a `PROJECT.md` there. Refuses (exit 1) if `project_dir/PROJECT.md` already exists, unless `--force`. Reads only `subdirs`/`project_md_prompts` (same two fields `scaffold_workspace.py` reads) -- any template works in either mode unchanged.

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

`init_workspace.py` only reads `template_id`/`label`/`workspace_subdirs`/`workspace_md_prompts`; `scaffold_workspace.py` and `init_project.py` only read `template_id`/`label`/`subdirs`/`project_md_prompts` -- a template must declare all 6 keys regardless of which mode it's used in, since every script validates independently and none guesses a default for a missing key.

## Bundled templates

| `template_id` | Maps to (registry cluster) | `subdirs` |
|---|---|---|
| `legal-practitioner` | Legal specializer cluster (`contract-consistency-linter`, `contract-risk-log`, `office-doc-creator`) | `source`, `work`, `draft`, `deliverables`, `archives` |
| `media-content-creator` | GenVid media cluster (`media-anchor-profile`, `image/video/audio-generator-gemini`, `video-assembly-composer`, `html-poster-composer`, `media-pipeline-orchestrator`) | `source`, `anchors`, `generated`, `assembly`, `deliverables` |
| `educator` | Teacher tier (`lesson-plan-builder`, `assessment-builder`, `competency-rubric-builder`, `grading-and-feedback`, `grade-book-builder`, `parent-communication`) | `source`, `lesson-plans`, `assessments`, `grading`, `communication` |
| `brand-design-project` | Light Design cluster (`brand-identity-linter`, `light-logo-arranger`, `html-poster-composer`) | `source`, `brand-spec`, `layout`, `assets`, `deliverables` |
| `researcher-writer` | General-capability research cluster (`deep-research`, `literature-review`, `citation-management`, `exploratory-data-analysis`, `hypothesis-generation`, `office-doc-creator`, `peer-review`) | `source`, `research`, `analysis`, `draft`, `deliverables` |

Each `project_md_prompts` entry names the specific skill(s) for that step, in the order the cluster's own `SKILL.md`s document them chaining. Pick the closest match, or supply a custom `template.json` (same 6-key schema) for a workflow none of these cover.

## What this skill does NOT do

- Does not track project state (which step is done, what's overdue) -- `PROJECT.md`/`WORKSPACE.md` are static starting points, not a live dashboard. A user editing them afterward is expected and fine.
- Does not invent a template for a workflow with no real grounding -- either a directly-piloted practitioner workflow (`legal-practitioner`'s bar) or, since v0.3.0, a real already-verified skill cluster in this registry (the other 4 templates' bar, owner-authorized 2026-08-07). A template mapping to neither is still out of scope.
- Does not move or reorganize files after scaffolding -- purely a one-time directory+file creation step.
- Does not re-render `WORKSPACE.md`/`PROJECT.md` if the template changes after init/scaffold -- both are one-time snapshots.
- Does not call any LLM/AI API.

## Verified

Scaffolded a real workspace from `assets/templates/legal-practitioner/template.json` into a fresh `projects_root`: correct `project_YYYYMMDD_01` directory name (today's date), all 5 subdirectories created, `PROJECT.md` rendered with all 5 prompts in order with correct headings. Ran a second scaffold against the same `projects_root`/date immediately after: correctly produced `..._02`, no collision, first project's directory untouched. Ran with `--date 2020-01-01` twice: correctly produced `..._01` then `..._02` for that historical date, independent of today's-date sequence. Malformed template (missing `project_md_prompts` key) correctly refused (exit 2, naming the missing key); a `project_md_prompts` entry missing `text` correctly refused (exit 2, naming the index); nonexistent template path correctly refused (exit 2).

**v0.2.0 (2026-08-05), `init_workspace.py`**: initialized a fresh workspace root from the real `legal-practitioner` template -- `projects/` and `projects/_templates/` created, template copied to `projects/_templates/legal-practitioner/template.json`, `WORKSPACE.md` rendered with all 3 real `workspace_md_prompts` and the correct `scaffold_workspace.py` invocation line pointing at the local template copy. Ran `scaffold_workspace.py` against that local copy immediately after -- produced a correct `project_20260805_01/` with all 5 subdirs and `PROJECT.md`, confirming the two scripts chain end-to-end. Re-ran `init_workspace.py` on the same workspace without `--force` -- correctly refused (exit 1, named `WORKSPACE.md` already exists). Re-ran with `--force` -- correctly re-initialized (exit 0). A template missing `workspace_md_prompts` correctly refused (exit 2, naming the missing key).

**v0.2.1 (2026-08-05)**: re-ran `init_workspace.py` and confirmed the real generated `WORKSPACE.md` contains the "Shared resources (once per workspace, never per project)" section verbatim, positioned between "Starting a new project" and "Prompts" as intended, with the rest of the file (subdirs, prompts) unaffected.

**v0.3.0 (2026-08-07)**: `init_project.py` run for real against all 5 bundled templates -- each correctly created its own `subdirs` directly under a fresh `project_dir` plus a `PROJECT.md` with every `project_md_prompts` entry rendered in order, no `WORKSPACE.md`/`_templates/` copy created. Re-run without `--force` on an already-scaffolded `project_dir` correctly refused (exit 1, naming the existing `PROJECT.md`); re-run with `--force` correctly re-scaffolded. A template missing `project_md_prompts` correctly refused (exit 2, naming the missing key), matching `scaffold_workspace.py`'s existing refusal shape. The 4 new templates (`media-content-creator`, `educator`, `brand-design-project`, `researcher-writer`) were each validated as well-formed JSON and run end-to-end through all 3 scripts (`init_workspace.py` -> `scaffold_workspace.py` against the workspace's own template copy -> `init_project.py` standalone) -- all 15 runs (5 templates x 3 scripts) exited 0 with the expected subdirs/prompts.

## Known limitations (v0.3.0)

- Sequence-number scanning only looks at direct children of `projects_root` matching the exact `project_YYYYMMDD_NN` pattern -- a differently-named existing directory for the same conceptual project is invisible to it (by design: never guess an existing project is "the same one").
- No re-render path if a template's prompts change after a workspace/project was already initialized/scaffolded -- `WORKSPACE.md`/`PROJECT.md` are one-time snapshots, not regenerated automatically.
- `init_workspace.py`'s re-init detection only checks for `WORKSPACE.md` and the template-copy directory -- a workspace manually stripped of one but not the other is a state this script hasn't been tested against.
- `init_project.py`'s re-scaffold detection only checks for `PROJECT.md` -- a `project_dir` manually stripped of it but with subdirs already present will re-create only the missing subdirs plus a fresh `PROJECT.md` (subdirs use `mkdir(exist_ok=True)`, never destructive, but this specific partial-state case isn't separately tested).
- The 4 registry-cluster templates (v0.3.0) reflect this registry's own documented skill-chain order, not an outside practitioner's real day-to-day workflow the way `legal-practitioner` does -- a real user in one of these professions may still reorder/rename steps; treat `project_md_prompts` as a reasonable default checklist, not a verified process the way the legal template is.
