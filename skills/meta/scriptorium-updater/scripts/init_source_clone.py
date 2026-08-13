#!/usr/bin/env python3
"""One-time setup: clones the real Scriptorium repo
(github.com/thatlq1812/scriptorium, confirmed public 2026-08-07) into a
caller-chosen local directory -- the ongoing source `check_updates.py`/
`sync_skills.py` pull from. Wraps `git clone` via subprocess with a fixed
argument list (no shell=True, no string interpolation into a shell
command) -- same safety shape as `scout-harvester`'s `clone_candidate.py`,
not reused directly since that script's own safety invariant (refuse
cloning INSIDE the Scriptorium tree) doesn't apply here -- this clones
Scriptorium ITSELF into a separate location, not a third-party repo.

Usage:
    python init_source_clone.py <dest_dir>

Exit 0 = cloned, 1 = git clone itself failed (network/auth/etc, git's own
error surfaced), 2 = malformed args or dest_dir already exists/non-empty.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from git_utils import run_git  # noqa: E402

SCRIPTORIUM_URL = "https://github.com/thatlq1812/scriptorium.git"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dest_dir", type=Path)
    args = parser.parse_args()

    if shutil.which("git") is None:
        print("ERROR: git not found on PATH.", file=sys.stderr)
        return 2

    if args.dest_dir.exists() and any(args.dest_dir.iterdir()):
        print(f"REFUSED: {args.dest_dir} already exists and is not empty.", file=sys.stderr)
        return 2

    result = run_git(None, ["clone", "--depth", "1", SCRIPTORIUM_URL, str(args.dest_dir)])
    if result.returncode != 0:
        print(f"CLONE FAILED: {result.stderr.strip()}", file=sys.stderr)
        return 1

    print(f"OK: cloned Scriptorium -> {args.dest_dir}")
    print("Next: run check_updates.py against this directory to see if it's ever behind, and sync_skills.py to copy skills/ into your own project.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
