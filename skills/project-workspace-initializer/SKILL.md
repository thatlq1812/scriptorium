---
name: project-workspace-initializer
description: Scaffolds a date-indexed project workspace (`projects/project_YYYYMMDD_NN/`) with structured subdirectories (`source/`, `work/`, `draft/`, `deliverables/`, `archives/` by default, or whatever a profession template declares) plus a generated `PROJECT.md` control-panel file with pre-formulated prompts, so a non-tech user can drive the calling agent through a multi-step task without navigating the directory tree manually. `scaffold_workspace.py` reads a profession template (start from `assets/templates/legal-practitioner/template.json`), auto-increments the day's sequence number by scanning existing project directories (never guesses, never overwrites), and writes both the subdirectory tree and `PROJECT.md`. Use when starting a new real-world matter/project spanning multiple work sessions. Do NOT use this for a one-off single-file task.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, re, datetime, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29).'
metadata:
  domain: general
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in a real non-tech-user pilot (a legal-practitioner workspace deployment, recorded in docs/ROADMAP.md's 'New planned roadmap items' 2026-07-29 entry -- the pilot deployment itself is no longer directly accessible on this machine, so the already-recorded workflow description in ROADMAP.md is treated as the elicitation record, same discipline as any other written elicitation source in this registry). Directory-scaffolding mechanism lightly cross-checked against public conventions (cookiecutter's template+variables pattern) via a web survey, not cloned -- kept stdlib-only, no templating-engine dependency, since the actual need (fixed subdirectory set + a prompts file) doesn't require one. Only one real profession template exists so far (legal-practitioner, the actually-piloted one) -- no template invented for a profession with no real pilot."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["workspace"]
---

# project-workspace-initializer

A scaffolder, not a project-management tool: creates the directory structure and a starting `PROJECT.md`, then gets out of the way. No tracking, no state beyond the filesystem itself.

## Why this skill, and why this scope

A real non-tech user (a legal practitioner, piloted directly) working with an agent across a multi-session matter kept losing track of which files were source material, which were in-progress drafts, and which were final deliverables -- and re-explaining the workflow to the agent at the start of every session. The fix isn't a database or a UI, it's the same idea `legal-form-filler`/`personal-profile-manager` already use for other problems: a generic engine (the scaffolder) driven by caller-supplied specifics (the profession template), so the mechanism doesn't need to know anything about any specific profession, and a new profession template can be added without touching the script.

Only the legal-practitioner template exists right now, because that's the only profession with a real pilot behind it -- adding a template for a profession with no real workflow behind it would be inventing process, the same thing `legal-form-filler` explicitly declined to do for "which form applies to a procedure."

## Run

```bash
python scripts/scaffold_workspace.py <template.json> <projects_root> [--date YYYY-MM-DD]
```

Start from `assets/templates/legal-practitioner/template.json`. `projects_root` is the parent directory under which `project_YYYYMMDD_NN/` gets created (e.g. `projects/` in the user's own workspace). The sequence number `NN` is derived by scanning `projects_root` for existing `project_<same-date>_NN` directories and taking `max+1` -- if none exist yet for that date, starts at `01`. `--date` overrides today's date (useful for scripted testing or backfilling); omit it in normal use.

Output: the new project directory with the template's declared subdirectories (defaults to `source/`, `work/`, `draft/`, `deliverables/`, `archives/` in the legal-practitioner template, but a template can declare any subdirectory list) plus a `PROJECT.md` rendering each of the template's `project_md_prompts` as a heading + instruction block.

### Template schema

```json
{
  "template_id": "string, matches the folder name under assets/templates/",
  "label": "human-readable label, used in PROJECT.md's title",
  "subdirs": ["source", "work", "draft", "deliverables", "archives"],
  "project_md_prompts": [
    {"heading": "string", "text": "string, the pre-formulated instruction for this step"}
  ]
}
```

## What this skill does NOT do

- Does not track project state (which step is done, what's overdue) -- `PROJECT.md` is a static starting point, not a live dashboard. A user editing it afterward is expected and fine.
- Does not invent a template for a profession with no real elicitation source -- see "Why this skill" above. Adding a new template requires the same discipline as adding a new niche-specializer skill (`CLAUDE.md` principle 4): a real practitioner workflow, not a guess.
- Does not move or reorganize files after scaffolding -- purely a one-time directory+file creation step.
- Does not call any LLM/AI API.

## Verified

Scaffolded a real workspace from `assets/templates/legal-practitioner/template.json` into a fresh `projects_root`: correct `project_YYYYMMDD_01` directory name (today's date), all 5 subdirectories created, `PROJECT.md` rendered with all 5 prompts in order with correct headings. Ran a second scaffold against the same `projects_root`/date immediately after: correctly produced `..._02`, no collision, first project's directory untouched. Ran with `--date 2020-01-01` twice: correctly produced `..._01` then `..._02` for that historical date, independent of today's-date sequence. Malformed template (missing `project_md_prompts` key) correctly refused (exit 2, naming the missing key); a `project_md_prompts` entry missing `text` correctly refused (exit 2, naming the index); nonexistent template path correctly refused (exit 2).

## Known limitations (v0.1.0)

- Sequence-number scanning only looks at direct children of `projects_root` matching the exact `project_YYYYMMDD_NN` pattern -- a differently-named existing directory for the same conceptual project is invisible to it (by design: never guess an existing project is "the same one").
- No re-render path if a template's `project_md_prompts` change after a project was already scaffolded -- `PROJECT.md` is a one-time snapshot, not regenerated automatically.
- Only one real profession template (`legal-practitioner`) exists; adding more is the next open step once a real pilot exists for another profession (see `UPGRADE_PLAN_20260729.md` Item 2).
