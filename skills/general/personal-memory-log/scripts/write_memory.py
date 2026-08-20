#!/usr/bin/env python3
"""Append (or update) one memory entry under personal/memory/.

Writes <memory_dir>/<name>.md (6-key-frontmatter-style: name/description/
metadata.type) and keeps <memory_dir>/MEMORY.md's one-line-per-entry index in
sync -- inserting a new index line, or replacing the existing one in place if
`--name` already has an entry (so re-running this on the same slug updates
the entry instead of duplicating its index line).

`--type` is exactly one of `user` | `feedback` | `project` | `reference`
(the same 4-way taxonomy this skill's own SKILL.md documents) -- refused
otherwise, never guessed. Body content is required and non-empty (a memory
entry with no content is not a real memory) -- pass it inline with --body or
from a file with --body-file (useful for multi-line content from a shell
that mangles embedded newlines).

Usage:
    python write_memory.py <memory_dir> --name <slug> --type <user|feedback|project|reference> \\
        --description <one-line description> (--body <text> | --body-file <path>) [--force]

Exit 0 = written, 1 = entry already exists (no --force) or memory_dir isn't
initialized yet (run init_memory.py first), 2 = bad arguments.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_TYPES = ("user", "feedback", "project", "reference")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
INDEX_LINE_MAX = 150


def _index_line(name: str, description: str) -> str:
    prefix = f"- [{name}]({name}.md) — "
    budget = INDEX_LINE_MAX - len(prefix)
    hook = description if len(description) <= budget else description[: max(budget - 3, 0)].rstrip() + "..."
    return prefix + hook


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("memory_dir", help="Path to the memory directory (e.g. personal/memory)")
    parser.add_argument("--name", required=True, help="Slug for this entry -- lowercase-kebab-case, becomes <name>.md")
    parser.add_argument("--type", required=True, choices=VALID_TYPES, help="One of: " + ", ".join(VALID_TYPES))
    parser.add_argument("--description", required=True, help="One-line summary, used as the index hook")
    parser.add_argument("--body", help="Entry body content (mutually exclusive with --body-file)")
    parser.add_argument("--body-file", help="Path to a file holding the entry body content")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing entry with this name")
    args = parser.parse_args()

    if not SLUG_RE.match(args.name):
        print(f"ERROR: --name '{args.name}' must match {SLUG_RE.pattern} (lowercase kebab-case).", file=sys.stderr)
        return 2
    if bool(args.body) == bool(args.body_file):
        print("ERROR: exactly one of --body or --body-file is required.", file=sys.stderr)
        return 2

    memory_dir = Path(args.memory_dir)
    index_path = memory_dir / "MEMORY.md"
    if not index_path.is_file():
        print(f"ERROR: {index_path} does not exist. Run init_memory.py first.", file=sys.stderr)
        return 1

    if args.body_file:
        body_path = Path(args.body_file)
        if not body_path.is_file():
            print(f"ERROR: --body-file {body_path} not found.", file=sys.stderr)
            return 2
        body = body_path.read_text(encoding="utf-8").strip()
    else:
        body = args.body.strip()
    if not body:
        print("ERROR: entry body is empty.", file=sys.stderr)
        return 2

    entry_path = memory_dir / f"{args.name}.md"
    if entry_path.exists() and not args.force:
        print(f"ERROR: {entry_path} already exists. Use --force to update it.", file=sys.stderr)
        return 1

    entry_text = (
        "---\n"
        f"name: {args.name}\n"
        f"description: {args.description}\n"
        "metadata:\n"
        f"  type: {args.type}\n"
        "---\n"
        "\n"
        f"{body}\n"
    )
    entry_path.write_text(entry_text, encoding="utf-8", newline="\n")

    index_text = index_path.read_text(encoding="utf-8")
    lines = index_text.splitlines()
    new_line = _index_line(args.name, args.description)
    marker = f"]({args.name}.md)"
    replaced = False
    for i, line in enumerate(lines):
        if marker in line:
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        lines.append(new_line)
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(f"{'Updated' if replaced else 'Added'} {entry_path} and its MEMORY.md index line.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
