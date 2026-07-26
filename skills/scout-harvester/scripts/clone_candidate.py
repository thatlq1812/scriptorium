#!/usr/bin/env python3
"""Shallow-clone a GitHub repo candidate for closer inspection, once
scout-harvester's preliminary evaluation (github_scout.py) has picked it as
worth reading in full. Wraps `git clone --depth 1` via subprocess with a
fixed argument list (no shell=True, no string interpolation into a shell
command) -- same safety shape as github_scout.py's `gh` wrapper.

This is deliberately NOT a general git-automation tool -- it does exactly
one thing (shallow clone by owner/repo slug into a caller-chosen directory
OUTSIDE this repo) and refuses the one dangerous default (cloning into the
Scriptorium repo tree itself, which would create a nested git repo and risk
accidentally committing third-party code).

Cloning is for REFERENCE/EVALUATION ONLY. It is not a license decision --
every candidate still needs license-compliance-check before any pattern or
code from it is used in a Scriptorium skill.

Usage:
    python clone_candidate.py <owner/repo> <dest_dir> [--ref <branch-or-tag>]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

SLUG_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?/[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")


def require_git() -> None:
    if shutil.which("git") is None:
        sys.exit("git not found on PATH.")


def is_inside_this_repo(dest: Path) -> bool:
    """True if dest resolves under the Scriptorium repo root (cwd must be
    the repo root, matching every other script's documented run convention)."""
    repo_root = Path.cwd().resolve()
    if not (repo_root / ".git").exists():
        return False  # not running from a repo root we can check against -- don't block
    try:
        dest.resolve().relative_to(repo_root)
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug", help="owner/repo, e.g. mermaid-js/mermaid")
    parser.add_argument("dest_dir", type=Path)
    parser.add_argument("--ref", default=None, help="branch or tag to clone (default: repo's default branch)")
    args = parser.parse_args()

    require_git()

    if not SLUG_RE.match(args.slug):
        print(f"REFUSED: {args.slug!r} doesn't look like a valid 'owner/repo' slug.", file=sys.stderr)
        return 2

    if is_inside_this_repo(args.dest_dir):
        print(
            f"REFUSED: {args.dest_dir} resolves inside the Scriptorium repo tree -- "
            "cloning a third-party repo in here would nest a second .git directory and "
            "risk accidentally committing candidate code. Clone into an external directory "
            "(e.g. the scratchpad) instead.",
            file=sys.stderr,
        )
        return 2

    if args.dest_dir.exists() and any(args.dest_dir.iterdir()):
        print(f"REFUSED: {args.dest_dir} already exists and is not empty.", file=sys.stderr)
        return 2

    url = f"https://github.com/{args.slug}.git"
    cmd = ["git", "clone", "--depth", "1"]
    if args.ref:
        cmd += ["--branch", args.ref]
    cmd += [url, str(args.dest_dir)]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"CLONE FAILED: {result.stderr.strip()}", file=sys.stderr)
        return 1

    print(f"OK: cloned {args.slug} -> {args.dest_dir}")
    print(
        "Reminder: this is for reference/evaluation only, not a license decision. "
        "Run license-compliance-check before using any pattern or code from this clone.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
