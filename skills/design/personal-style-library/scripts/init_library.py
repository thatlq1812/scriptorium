#!/usr/bin/env python3
"""Scaffold a personal style-library directory: 4 category subfolders under
<personal_dir>/style_library/. No seed data is written -- categories start
empty, since a real palette/style/motif-set/font-pairing is always the
caller's own real reference material, never invented content.

Usage:
    python init_library.py <personal_dir> [--force]

Exit 0 = scaffolded (or already exists with --force), 1 = already exists
without --force, 2 = malformed args.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

CATEGORIES = ("palettes", "styles", "motifs", "fonts")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("personal_dir")
    parser.add_argument("--force", action="store_true", help="Proceed even if style_library/ already exists.")
    args = parser.parse_args()

    library_root = Path(args.personal_dir) / "style_library"

    if library_root.exists() and not args.force:
        print(f"ERROR: {library_root} already exists. Use --force to proceed anyway (existing entries are never touched).", file=sys.stderr)
        return 1

    for category in CATEGORIES:
        (library_root / category).mkdir(parents=True, exist_ok=True)

    print(f"Initialized style library at {library_root}")
    for category in CATEGORIES:
        print(f"  {category}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
