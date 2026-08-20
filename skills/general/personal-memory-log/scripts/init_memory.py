#!/usr/bin/env python3
"""Scaffold personal/memory/ -- a local, append-only memory log distinct from
personal-profile-manager's own personal/profile.json (fixed identity/org/
contact schema).

Creates <memory_dir>/ (if missing) and an index file, <memory_dir>/MEMORY.md,
with a fixed header and an empty entry list. write_memory.py is the only
script that ever appends to the index afterward -- this script only ever
creates the starting state, mirroring init_profile.py's own scaffold/refuse
split (never a partial merge into an existing file).

Usage:
    python init_memory.py <memory_dir> [--force]

Exit 0 = created, 1 = memory_dir/MEMORY.md already exists (no --force), 2 = bad arguments.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

MEMORY_MD_HEADER = (
    "# Memory Index\n"
    "\n"
    "One line per entry, newest-relevant-first is not required -- keep entries "
    "organized by topic, not chronologically. Each line links to the entry's "
    "own file under this same directory. Do not write memory content directly "
    "here; write_memory.py maintains this file, one line per entry, "
    "under ~150 characters each.\n"
    "\n"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("memory_dir", help="Path to create as the memory directory (e.g. personal/memory)")
    parser.add_argument("--force", action="store_true", help="Re-initialize even if MEMORY.md already exists")
    args = parser.parse_args()

    memory_dir = Path(args.memory_dir)
    index_path = memory_dir / "MEMORY.md"

    if index_path.exists() and not args.force:
        print(f"ERROR: {index_path} already exists. Use --force to re-initialize.", file=sys.stderr)
        return 1

    memory_dir.mkdir(parents=True, exist_ok=True)
    index_path.write_text(MEMORY_MD_HEADER, encoding="utf-8", newline="\n")
    print(f"Created {index_path}. Use write_memory.py to add entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
