#!/usr/bin/env python3
"""Scaffold a date-indexed project workspace from a profession template.

Creates <projects_root>/project_YYYYMMDD_NN/ with the template's declared
subdirectories plus a generated PROJECT.md control-panel file (the
pre-formulated prompts a non-tech user drives the agent with, so they don't
have to navigate the directory tree manually).

Sequence numbering (NN) is derived by scanning <projects_root> for existing
project_<date>_NN directories and taking max+1 -- never guessed, never
silently reused, refuses rather than overwriting an existing directory.

Usage:
    python scaffold_workspace.py <template.json> <projects_root> [--date YYYY-MM-DD]

Exit 0 = scaffolded, 1 = target already exists (should be unreachable given
auto-increment, kept as a defensive refusal), 2 = malformed template/args.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

PROJECT_DIR_RE = re.compile(r"^project_(\d{8})_(\d{2})$")
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


def _next_sequence(projects_root: Path, date_str: str) -> str:
    max_seq = 0
    if projects_root.exists():
        for entry in projects_root.iterdir():
            if not entry.is_dir():
                continue
            m = PROJECT_DIR_RE.match(entry.name)
            if m and m.group(1) == date_str:
                max_seq = max(max_seq, int(m.group(2)))
    return f"{max_seq + 1:02d}"


def _render_project_md(template: dict, project_dir_name: str) -> str:
    lines = [
        f"# {project_dir_name} — {template['label']}",
        "",
        f"Scaffolded from template `{template['template_id']}` by `project-workspace-initializer`.",
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template_path")
    parser.add_argument("projects_root")
    parser.add_argument("--date", help="Override the date used in the folder name (YYYY-MM-DD). Defaults to today.")
    args = parser.parse_args()

    template_path = Path(args.template_path)
    if not template_path.exists():
        print(f"ERROR: template not found: {template_path}", file=sys.stderr)
        return 2
    template = _load_template(template_path)

    if args.date:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
            print(f"ERROR: --date must be YYYY-MM-DD, got {args.date!r}", file=sys.stderr)
            return 2
        date_str = args.date.replace("-", "")
    else:
        date_str = date.today().strftime("%Y%m%d")

    projects_root = Path(args.projects_root)
    seq = _next_sequence(projects_root, date_str)
    project_dir_name = f"project_{date_str}_{seq}"
    project_dir = projects_root / project_dir_name

    if project_dir.exists():
        print(f"ERROR: {project_dir} already exists (sequence collision) -- refusing to overwrite.", file=sys.stderr)
        return 1

    for sub in template["subdirs"]:
        (project_dir / sub).mkdir(parents=True, exist_ok=True)

    project_md_text = _render_project_md(template, project_dir_name)
    (project_dir / "PROJECT.md").write_text(project_md_text, encoding="utf-8", newline="\n")

    print(f"Scaffolded {project_dir}")
    print(f"  subdirs: {', '.join(template['subdirs'])}")
    print(f"  PROJECT.md: {project_dir / 'PROJECT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
