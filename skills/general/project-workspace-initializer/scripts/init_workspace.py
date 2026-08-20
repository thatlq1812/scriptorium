#!/usr/bin/env python3
"""Initialize a workspace root from a profession template -- the one-time
step above scaffold_workspace.py's per-project step.

Creates <workspace_root>/ (if missing) with the template's declared
workspace-level subdirectories, copies the template itself into
<workspace_root>/projects/_templates/<template_id>/ so later
scaffold_workspace.py runs can reference a local copy instead of this
repo's path, and writes 2 control-panel files: WORKSPACE.md (the
workspace-level counterpart of PROJECT.md, rendering the template's
workspace_md_prompts) and AGENTS.md (v0.4.0 -- the root file most harnesses
read at every session start, carrying the fixed, profession-agnostic
operating rules every workspace built by this skill needs regardless of
which template it used).

Grounded in the real non-tech-user pilot recorded in docs/ROADMAP.md's
2026-07-29 entry ("Project Workspace Scaffolder Skill"): the pilot's own
`d:/my-workspace` deployment used a `projects/` root with a
`projects/_templates/` template location -- this script builds that
top-level structure; scaffold_workspace.py builds each dated project inside
it. AGENTS.md's content (v0.4.0, thatlq1812-directed 2026-08-14, PROJECT.md
change request item 3b) is grounded in a second real pilot workspace review
(`D:\\AppData\\my_workspace`) that surfaced this exact gap: the workspace's
own hand-written AGENTS.md was 3 short paragraphs with no naming convention,
no rule against replying with a deliverable inline instead of scaffolding a
real project, and no instruction to keep `personal/` up to date -- real
symptoms thatlq1812 traced back to this skill never having generated
AGENTS.md at all (the file predates this version, written ad hoc by
whichever agent set that workspace up).

Usage:
    python init_workspace.py <template.json> <workspace_root> [--force]

Exit 0 = initialized, 1 = workspace already initialized (WORKSPACE.md,
AGENTS.md, or the template copy destination already exists) without
--force, 2 = malformed template/args.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_TEMPLATE_KEYS = {"template_id", "label", "workspace_subdirs", "workspace_md_prompts"}

# Fixed, profession-agnostic workspace-root dirs created regardless of which
# template is used -- distinct from a template's own `workspace_subdirs`
# (which only ever declares `projects`/`projects/_templates`). Added v0.5.0
# (thatlq1812, 2026-08-15, START_HERE_INSTRUCT.md): a real onboarding needs
# these 3 to exist from the start, not only whatever a specific profession
# template happens to declare. `personal/` matches personal-profile-manager's
# own `personal/profile.json` convention exactly (previously documented here
# as `personals/`, a naming mismatch never actually created by either skill
# -- fixed same round).
FIXED_WORKSPACE_SUBDIRS = ["data", "documents", "personal"]


def _load_template(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict) or not REQUIRED_TEMPLATE_KEYS.issubset(data):
        print(f"ERROR: template must be an object with keys {sorted(REQUIRED_TEMPLATE_KEYS)}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data["workspace_subdirs"], list) or not data["workspace_subdirs"]:
        print("ERROR: template 'workspace_subdirs' must be a non-empty list.", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data["workspace_md_prompts"], list) or not data["workspace_md_prompts"]:
        print("ERROR: template 'workspace_md_prompts' must be a non-empty list.", file=sys.stderr)
        sys.exit(2)
    for i, prompt in enumerate(data["workspace_md_prompts"]):
        if not isinstance(prompt, dict) or "heading" not in prompt or "text" not in prompt:
            print(f"ERROR: workspace_md_prompts[{i}] must have 'heading' and 'text'.", file=sys.stderr)
            sys.exit(2)
    return data


def _render_workspace_md(template: dict, template_copy_path: Path) -> str:
    lines = [
        f"# {template['label']} — Workspace",
        "",
        f"Initialized from template `{template['template_id']}` by `project-workspace-initializer`.",
        "",
        "## Subdirectories",
        "",
    ]
    for sub in FIXED_WORKSPACE_SUBDIRS:
        lines.append(f"- `{sub}/`")
    for sub in template["workspace_subdirs"]:
        lines.append(f"- `{sub}/`")
    lines += [
        "",
        "`data/` and `documents/` hold reference material shared across projects "
        "(datasets, source documents that aren't specific to one matter) -- project-"
        "specific source material still belongs inside that project's own `source/` "
        "subdirectory, not here. `documents/` has no fixed subfolder structure -- "
        "organize it into subfolders that fit what this specific workspace owner "
        "actually deals with (inferred from the tasks done here, not assigned "
        "upfront); check what's already there before adding a new top-level "
        "subfolder. `personal/` is this workspace owner's profile store "
        "(`personal-profile-manager`) and running memory log "
        "(`personal-memory-log`, see `AGENTS.md`'s \"Personal memory\" section).",
        "",
        "## Starting a new project",
        "",
        f"Run `scaffold_workspace.py {template_copy_path.as_posix()} projects/ --name <slug>` "
        "(from `project-workspace-initializer`) to create a new project directory "
        "under `projects/` using this workspace's own copy of the template -- no "
        "need to reference the skill's own repo path again. Produces "
        "`projects/<YYYYMMDD>-<slug>/` (see `AGENTS.md`'s \"Project structure\" "
        "section for the full naming convention).",
        "",
        "## Shared resources (once per workspace, never per project)",
        "",
        "Two things belong exactly once at this workspace's root, not duplicated "
        "inside any `projects/<YYYYMMDD>-<name>/` subdirectory:",
        "",
        "- **Skills**: if this workspace was set up from a `skill-exporter` bundle, "
        "install the skills once here (see the bundle's `MANIFEST.md` \"Where to "
        "install\" section for your harness's convention, e.g. `.claude/skills/`, "
        "`.agents/skills/`) -- do not re-copy or re-link skills into each new "
        "project directory.",
        "- **Python environment**: if any skill you use here needs non-stdlib "
        "Python packages, bootstrap ONE shared virtual environment at this "
        "workspace's root (not one per project) the first time it's actually "
        "needed, and always invoke scripts through that venv's own interpreter, "
        "not a bare `python`/`python3` -- silently falling back to system Python "
        "without the right packages installed is the most common real failure "
        "mode with these skills.",
        "",
        "## Prompts",
        "",
    ]
    for prompt in template["workspace_md_prompts"]:
        lines.append(f"### {prompt['heading']}")
        lines.append("")
        lines.append(prompt["text"])
        lines.append("")
    return "\n".join(lines)


def _render_agents_md(template: dict, template_copy_path: Path) -> str:
    lines = [
        "# AGENTS.md",
        "",
        f"This workspace ({template['label']}) is managed by Scriptorium Workspace "
        "(`project-workspace-initializer`). Read this file in full before doing any "
        "non-trivial work here -- it is not optional context, it is the operating "
        "contract for this workspace.",
        "",
        "**This is a live filesystem workspace, not a chat session.** The user is "
        "non-technical and expects real files (documents, spreadsheets, decks) to "
        "exist afterward, not just text in a reply. Every rule below exists because "
        "a real deployment hit exactly the failure it corrects -- follow them.",
        "",
        "## Skill registry",
        "",
        "A local skill registry lives at `skills/<skill-name>/SKILL.md` (index: "
        "`registry/skills.json`, or the flat `skills/` directory this bundle installed "
        "into -- see this workspace's own skill-install location). Before doing a "
        "non-trivial task, check whether a skill already covers it (grep `name`/"
        "`description` fields) and read that skill's `SKILL.md` in full before using "
        "it -- required inputs, invocation, and known limitations are documented there, "
        "not guessed.",
        "",
        "## Root cleanup -- no file stays loose at this workspace's root",
        "",
        "This workspace's root is meant to hold only `data/`, `documents/`, `personal/`, "
        "`projects/`, `AGENTS.md`/`WORKSPACE.md`, and housekeeping dot-directories -- "
        "never a loose working file. A user commonly drops a file (or several) directly "
        "at the root and then asks about it in chat instead of placing it somewhere "
        "first; the moment such a file is involved in a task, relocate it as part of "
        "doing that task, don't leave it at root:",
        "",
        "- Belongs to one specific matter (existing or new) -> move it into that "
        "project's own `source/` subdirectory (reuse an existing project if it's a "
        "continuation of that project's work, otherwise scaffold a new one first).",
        "- Reusable raw material not specific to one project -> move it into `data/`.",
        "- Already-processed/normalized material -> move it into `documents/`.",
        "",
        "Move the file (never copy -- a stray duplicate left at root defeats the "
        "point), then report in your reply what was moved and where. Do this without "
        "asking for confirmation first -- a cluttered root is a worse default than a "
        "file moved somewhere sensible.",
        "",
        "## Project structure -- mandatory, not a suggestion",
        "",
        "**Every piece of real work (a document, a dataset, a design, a deliverable of "
        "any kind) lives inside its own directory under `projects/`, never loose at "
        "`projects/`'s own root and never directly at this workspace's root.** Use "
        "`scaffold_workspace.py` (from `project-workspace-initializer`, see below) to "
        "create it -- never `mkdir` a project directory by hand, and never write a "
        "deliverable file straight into `projects/` without first scaffolding a dated "
        "subdirectory for it, since the naming convention and `PROJECT.md` control "
        "panel both come from that script. A loose file sitting directly under "
        "`projects/` is always a mistake -- move it into a scaffolded project directory "
        "(scaffolding one first if none fits) rather than leaving it there.",
        "",
        "**Naming convention**: `projects/<YYYYMMDD>-<name>/`, or "
        "`projects/<YYYYMMDD>-<name>-v<N>/` if `<name>` was already used before --",
        "- `<YYYYMMDD>`: the date this specific project directory was scaffolded.",
        "- `<name>`: a lowercase kebab-case slug identifying the project (e.g. "
        "`hop-dong-internet`, `bao-cao-tong-ket-nam-hoc`) -- picked by whoever scaffolds "
        "it, not auto-generated; Vietnamese names should be transliterated to plain "
        "ASCII kebab-case (no diacritics, no spaces) same as the examples above.",
        "- `-v<N>`: appended automatically ONLY when `<name>` already exists under "
        "`projects/` (any date) -- a first-time name gets no suffix; re-scaffolding "
        "the same `<name>` later (a redo, a new round of the same matter) gets "
        "`-v2`, `-v3`, ... appended instead of colliding with the earlier attempt.",
        "",
        "**Archiving finished projects (convention, not automated)**: once a project "
        "under `projects/` is fully done and the user won't touch it again, move its "
        "directory into `projects/_archive/` (create it if it doesn't exist yet) to "
        "keep `projects/` itself easy to scan. No script does this automatically -- "
        "move it by hand when the user confirms a project is finished.",
        "",
        "```bash\n"
        f"python {template_copy_path.as_posix()} projects/ --name <slug> [--date YYYY-MM-DD]\n"
        "```",
        "",
        "## When a request implies a deliverable, create it as a real file -- do not just reply with it",
        "",
        "If a request asks for something that is normally a real artifact -- a contract, "
        "a report, a lesson plan, a slide deck, a poster, any document a human would "
        "expect to receive as a file -- and the user has NOT explicitly said something "
        "like \"just show me here\"/\"no need to save a file\", the correct response is: "
        "(1) scaffold or reuse a project directory for it (see above), (2) build the "
        "real output file inside that project using the appropriate skill (e.g. "
        "`office-doc-creator` for a real .docx/.pptx/.xlsx), and (3) report back what "
        "was created and where. Replying with the content typed directly into the chat "
        "instead of creating the file is the wrong default -- it throws away the whole "
        "point of this workspace's project structure and leaves nothing for the user to "
        "actually open, edit, or hand to someone else.",
        "",
        "## Personal/organization profile -- keep it up to date proactively",
        "",
        "`personal/` holds this workspace owner's reusable identity/organization/contact "
        "details (`personal-profile-manager`'s `profile.json`, optionally an "
        "`org_profile` section for letterhead/issuing-organization identity). Don't "
        "treat this as a passive lookup used only when a form explicitly asks for a "
        "field: whenever a task surfaces a durable identity/org/contact/style-preference "
        "fact the profile doesn't already have (a new signatory, a corrected address, a "
        "writing-style correction worth remembering), proactively propose updating "
        "`personal/profile.json` (via `personal-profile-manager`'s scripts) rather than "
        "letting the same detail get re-typed or re-asked next time. A skill producing "
        "reusable personal/org data as a side effect of its normal output should note "
        "that back into `personal/` too, not only whichever project it was working in.",
        "",
        "## Personal memory -- write it proactively, read it at the start of work",
        "",
        "`personal/memory/` (`personal-memory-log`) holds a running log of what you've "
        "learned about this workspace owner beyond identity/org/contact data -- "
        "preferences, working habits, ongoing project context, corrections to how you "
        "should work. If `personal/memory/MEMORY.md` exists, read it before doing "
        "non-trivial work, the same way you read this file. Write a new entry (via "
        "`personal-memory-log`'s `write_memory.py`, initializing the directory first "
        "with `init_memory.py` if it doesn't exist yet) whenever a task surfaces a "
        "durable fact worth remembering next time -- don't wait for the user to "
        "explicitly say \"remember this.\" Write only what was actually said or "
        "actually observed, never a guess.",
        "",
        "## Shared resources (once per workspace, never per project)",
        "",
        "- **Skills**: installed once at this workspace's own skill directory (see your "
        "harness's convention, e.g. `.claude/skills/`, `.agents/skills/`) -- never "
        "re-copied or re-linked per project.",
        "- **Python environment**: ONE shared virtual environment at this workspace's "
        "root (not one per project), bootstrapped the first time a skill actually needs "
        "non-stdlib packages -- always invoke scripts through that venv's own "
        "interpreter, never a bare `python`/`python3`.",
        "",
        "See `WORKSPACE.md` for this workspace's specific subdirectories and "
        f"`{template['label']}`-template prompts.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("template_path")
    parser.add_argument("workspace_root")
    parser.add_argument("--force", action="store_true", help="Re-initialize even if WORKSPACE.md or the template copy already exists.")
    args = parser.parse_args()

    template_path = Path(args.template_path)
    if not template_path.exists():
        print(f"ERROR: template not found: {template_path}", file=sys.stderr)
        return 2
    template = _load_template(template_path)

    workspace_root = Path(args.workspace_root)
    workspace_md_path = workspace_root / "WORKSPACE.md"
    agents_md_path = workspace_root / "AGENTS.md"
    template_copy_dir = workspace_root / "projects" / "_templates" / template["template_id"]

    if not args.force:
        if workspace_md_path.exists():
            print(f"ERROR: {workspace_md_path} already exists -- workspace already initialized. Use --force to re-initialize.", file=sys.stderr)
            return 1
        if agents_md_path.exists():
            print(f"ERROR: {agents_md_path} already exists -- workspace already initialized. Use --force to re-initialize.", file=sys.stderr)
            return 1
        if template_copy_dir.exists():
            print(f"ERROR: {template_copy_dir} already exists -- workspace already initialized. Use --force to re-initialize.", file=sys.stderr)
            return 1

    for sub in FIXED_WORKSPACE_SUBDIRS + template["workspace_subdirs"]:
        (workspace_root / sub).mkdir(parents=True, exist_ok=True)

    shutil.copytree(template_path.parent, template_copy_dir, dirs_exist_ok=args.force)
    template_copy_path = template_copy_dir / template_path.name

    workspace_md_text = _render_workspace_md(template, template_copy_path)
    workspace_md_path.write_text(workspace_md_text, encoding="utf-8", newline="\n")

    agents_md_text = _render_agents_md(template, template_copy_path)
    agents_md_path.write_text(agents_md_text, encoding="utf-8", newline="\n")

    print(f"Initialized workspace {workspace_root}")
    print(f"  subdirs: {', '.join(FIXED_WORKSPACE_SUBDIRS + template['workspace_subdirs'])}")
    print(f"  template copy: {template_copy_dir}")
    print(f"  WORKSPACE.md: {workspace_md_path}")
    print(f"  AGENTS.md: {agents_md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
