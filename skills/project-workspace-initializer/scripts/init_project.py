#!/usr/bin/env python3
"""Scaffold a single standalone project from a profession template -- no
workspace wrapper.

Unlike scaffold_workspace.py (which assumes a pre-initialized
<workspace_root>/projects/ root and date-indexes each new matter as
project_YYYYMMDD_NN under it), this creates the template's subdirectories
and a PROJECT.md directly at a caller-given <project_dir>, with no
WORKSPACE.md, no projects/_templates/ template copy, and no date/sequence
naming -- for the case where a single one-off project is the whole unit of
work, not one matter among many inside a shared workspace.

Reuses the exact same template.json fields scaffold_workspace.py already
reads (subdirs, project_md_prompts) -- a template written for one mode works
unchanged in the other; init_workspace.py-only fields (workspace_subdirs,
workspace_md_prompts) are not required here and are ignored if present.

Usage:
    python init_project.py <template.json> <project_dir> [--force]

Exit 0 = scaffolded, 1 = project_dir already has a PROJECT.md (already
scaffolded) without --force, 2 = malformed template/args.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_TEMPLATE_KEYS = {"template_id", "label", "subdirs", "project_md_prompts"}


def _load_template(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict) or not REQUIRED_TEMPLATE_KEYS.issubset(data):
        print(f"ERROR: template must be an object with keys {sorted(REQUIRED_TEMPLATE_KEYS)}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data["subdirs"], list) or not data["subdirs"]:
        print("ERROR: template 'subdirs' must be a non-empty list.", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data["project_md_prompts"], list) or not data["project_md_prompts"]:
        print("ERROR: template 'project_md_prompts' must be a non-empty list.", file=sys.stderr)
        sys.exit(2)
    for i, prompt in enumerate(data["project_md_prompts"]):
        if not isinstance(prompt, dict) or "heading" not in prompt or "text" not in prompt:
            print(f"ERROR: project_md_prompts[{i}] must have 'heading' and 'text'.", file=sys.stderr)
            sys.exit(2)
    return data


def _render_project_md(template: dict, project_dir_name: str) -> str:
    lines = [
        f"# {project_dir_name} — {template['label']}",
        "",
        f"Scaffolded as a standalone project from template `{template['template_id']}` "
        "by `project-workspace-initializer`'s `init_project.py` -- no workspace wrapper, "
        "no WORKSPACE.md, no date/sequence naming. This directory is the whole project.",
        "",
        "## Subdirectories",
        "",
    ]
    for sub in template["subdirs"]:
        lines.append(f"- `{sub}/`")
    lines.append("")
    lines.append("## Prompts")
    lines.append("")
    for prompt in template["project_md_prompts"]:
        lines.append(f"### {prompt['heading']}")
        lines.append("")
        lines.append(prompt["text"])
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("template_path")
    parser.add_argument("project_dir")
    parser.add_argument("--force", action="store_true", help="Re-scaffold even if PROJECT.md already exists at project_dir.")
    args = parser.parse_args()

    template_path = Path(args.template_path)
    if not template_path.exists():
        print(f"ERROR: template not found: {template_path}", file=sys.stderr)
        return 2
    template = _load_template(template_path)

    project_dir = Path(args.project_dir)
    project_md_path = project_dir / "PROJECT.md"

    if project_md_path.exists() and not args.force:
        print(f"ERROR: {project_md_path} already exists -- project already scaffolded. Use --force to re-scaffold.", file=sys.stderr)
        return 1

    for sub in template["subdirs"]:
        (project_dir / sub).mkdir(parents=True, exist_ok=True)

    project_md_text = _render_project_md(template, project_dir.name or str(project_dir))
    project_md_path.write_text(project_md_text, encoding="utf-8", newline="\n")

    print(f"Scaffolded standalone project {project_dir}")
    print(f"  subdirs: {', '.join(template['subdirs'])}")
    print(f"  PROJECT.md: {project_md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
