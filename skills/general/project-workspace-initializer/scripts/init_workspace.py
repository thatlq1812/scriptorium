#!/usr/bin/env python3
"""Initialize a workspace root from a profession template -- the one-time
step above scaffold_workspace.py's per-project step.

Creates <workspace_root>/ (if missing) with the template's declared
workspace-level subdirectories, copies the template itself into
<workspace_root>/projects/_templates/<template_id>/ so later
scaffold_workspace.py runs can reference a local copy instead of this
repo's path, and writes a WORKSPACE.md control-panel file (the workspace-level
counterpart of PROJECT.md) with the template's workspace_md_prompts.

Grounded in the real non-tech-user pilot recorded in docs/ROADMAP.md's
2026-07-29 entry ("Project Workspace Scaffolder Skill"): the pilot's own
`d:/my-workspace` deployment used a `projects/` root with a
`projects/_templates/` template location -- this script builds that
top-level structure; scaffold_workspace.py builds each dated project inside
it.

Usage:
    python init_workspace.py <template.json> <workspace_root> [--force]

Exit 0 = initialized, 1 = workspace already initialized (WORKSPACE.md or the
template copy destination already exists) without --force, 2 = malformed
template/args.
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
    for sub in template["workspace_subdirs"]:
        lines.append(f"- `{sub}/`")
    lines += [
        "",
        "## Starting a new project",
        "",
        f"Run `scaffold_workspace.py {template_copy_path.as_posix()} projects/` "
        "(from `project-workspace-initializer`) to create a new dated project "
        "directory under `projects/` using this workspace's own copy of the "
        "template -- no need to reference the skill's own repo path again.",
        "",
        "## Shared resources (once per workspace, never per project)",
        "",
        "Two things belong exactly once at this workspace's root, not duplicated "
        "inside any `projects/project_YYYYMMDD_NN/` subdirectory:",
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
    template_copy_dir = workspace_root / "projects" / "_templates" / template["template_id"]

    if not args.force:
        if workspace_md_path.exists():
            print(f"ERROR: {workspace_md_path} already exists -- workspace already initialized. Use --force to re-initialize.", file=sys.stderr)
            return 1
        if template_copy_dir.exists():
            print(f"ERROR: {template_copy_dir} already exists -- workspace already initialized. Use --force to re-initialize.", file=sys.stderr)
            return 1

    for sub in template["workspace_subdirs"]:
        (workspace_root / sub).mkdir(parents=True, exist_ok=True)

    shutil.copytree(template_path.parent, template_copy_dir, dirs_exist_ok=args.force)
    template_copy_path = template_copy_dir / template_path.name

    workspace_md_text = _render_workspace_md(template, template_copy_path)
    workspace_md_path.write_text(workspace_md_text, encoding="utf-8", newline="\n")

    print(f"Initialized workspace {workspace_root}")
    print(f"  subdirs: {', '.join(template['workspace_subdirs'])}")
    print(f"  template copy: {template_copy_dir}")
    print(f"  WORKSPACE.md: {workspace_md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
