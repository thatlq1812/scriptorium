# Start Here — Scriptorium Skill Snapshot

This is a raw snapshot of Scriptorium's `skills/` + `registry/` folders, zipped together for onboarding a brand-new workspace end to end. **You (the agent) are expected to drive this whole process autonomously** for a non-technical user — don't wait for them to run commands themselves; run the steps below, ask them only the questions marked "ask the user", and report back what you did. This is a live filesystem setup, not a chat exercise: every step below produces real files/directories, not a description of what could be done.

Prefer `python skills/meta/skill-exporter/scripts/export_bundle.py --all -o bundle.zip` over a raw folder zip when you have the choice: it applies the same license/security/paused gate this snapshot skips, and additionally writes `MANIFEST.md`/`dependency-tree.md`/`skills.lock` for provenance. This file exists for the times a raw zip is faster and you're doing the gating yourself.

Follow the steps below **in order**. Step 8 tells you to delete this file, `skills/`, and `registry/` — do that last, not before.

## 1. Install the skills, then remove the source copies

Copy each folder under `skills/` into your agent harness's own skill directory. Known conventions:

- **Claude Code**: `.claude/skills/<skill_id>/`
- **goose (Agent Client Protocol)**: `.agents/skills/<skill_id>/` (also checks `.goose/skills/` and `.claude/skills/` project-local, plus a few global paths under `$HOME`)
- **Cursor**: `.cursor/skills/<skill_id>/` (per Cursor's own docs)

If you're not sure which directory your harness uses, check its own docs. Install exactly once at your **workspace root** -- if you manage multiple projects under one workspace, do not re-copy or re-link `skills/` into each individual project directory.

Once the copy is installed and readable from its new location, delete the source `skills/` and `registry/` folders (and the `.zip`/snapshot they came from, if still around) right now — don't leave a second, increasingly-stale copy sitting in the workspace root while you do the rest of this setup. `registry/skills.json` was only useful for browsing what was available before you decided what to keep; nothing at runtime reads it from this location.

## 2. Ask the user about themselves and their work

**Ask the user** (don't guess or skip this): their name/role, their organization (if any), and what kind of work they'll actually use this workspace for — day to day tasks, the kind of documents/deliverables they produce, who they produce them for. Ask thoroughly and offer concrete suggestions grounded in what this registry's skills actually cover (see `skills/general/project-workspace-initializer/SKILL.md`'s "Bundled templates" table for the profession clusters already mapped: legal practitioner, media/content creator, educator, brand/design, researcher/writer) rather than asking abstractly — e.g. "you mentioned drafting contracts — that matches the legal-practitioner template, which chains `contract-consistency-linter`/`contract-risk-log`/`office-doc-creator`; does that match your actual workflow, or is it different?".

Take their answer on identity/contact details and scaffold their profile now:

```bash
python skills/general/personal-profile-manager/scripts/init_profile.py personal/profile.json [--with-org-profile]
```

(`--with-org-profile` if they issue documents on behalf of an organization/letterhead, not just as an individual — see that skill's own `SKILL.md`.)

## 3. Set up the workspace structure, tailored to what you just learned

Pick the closest-matching bundled template from `skills/general/project-workspace-initializer/assets/templates/` based on step 2's answers (or write a custom `template.json`, same 6-key schema, if none fit). Then:

```bash
python skills/general/project-workspace-initializer/scripts/init_workspace.py <template.json> .
```

This creates `data/`, `documents/`, `personal/`, `projects/` (+ `projects/_templates/`), copies the template into `projects/_templates/<template_id>/`, and writes `WORKSPACE.md` + `AGENTS.md` (the fixed operating rules — naming convention, "create a real file, don't just reply with content" rule, keep `personal/` current, shared venv/skills reminder). Read the generated `AGENTS.md` yourself once it exists — it is this workspace's actual operating contract from here on, not optional background.

**Now customize the copied template** at `projects/_templates/<template_id>/template.json` for what you actually learned in step 2 — don't leave the generic bundled default as-is if the user's real workflow differs from it (different subdirectories, different `project_md_prompts` steps, different skill references). A `template.json` is a reconfigurable checklist, not a fixed process; the bundled ones are a starting point, not the final word. This is the step that makes `scaffold_workspace.py` runs afterward actually produce something tailored, instead of a generic shell nobody ends up using.

## 4. Bootstrap the shared Python environment (only if the user will need it)

Some skills (e.g. `office-doc-creator`, `document-ai-structurer`, `browser-web-renderer`, `slide-deck-composer`, `gemini-generator`) need non-stdlib Python packages. If step 2's answers suggest the user will use one of these (document generation, media generation, web rendering are the common triggers), bootstrap now — see `skills/general/toolchain-bootstrap/SKILL.md` for the exact command. Bootstrap ONE shared venv at this workspace's root (not one per project, not one per skill), and always invoke scripts through that venv's own interpreter afterward, not a bare `python`/`python3` -- silently falling back to system Python without the right packages installed is the most common real failure mode with these skills. **On Windows, run the bootstrap through real PowerShell, never Git Bash/MSYS2** — `uv` misdetects the platform there and downloads an unusable Linux Python build.

If nothing the user described needs a non-stdlib package, skip this step — don't bootstrap a venv nobody will use.

## 5. Two rules to actually enforce from here on

These are already written into the generated `AGENTS.md`, restated here because they're the two failure modes most worth watching for with a non-technical user:

- **A request implying a deliverable gets a real file, not a chat reply.** If the user asks for something like "I need a leave-of-absence form", the correct response is a real `.docx` (via `office-doc-creator` or whichever skill applies) inside a scaffolded project — not the form's text typed into the conversation.
- **Every deliverable lives inside a scaffolded project directory under `projects/`, never loose at `projects/`'s own root.** Use `scaffold_workspace.py --name <slug>` to create one first; never `mkdir` by hand, never write a file straight into `projects/`.

## 6. Clean up

Once steps 1–5 are done, delete this file (`START_HERE.md`) from wherever you unzipped it — `skills/` and `registry/` should already be gone from step 1. What matters now lives in your harness's own skill directory, `AGENTS.md`, and `WORKSPACE.md`.
