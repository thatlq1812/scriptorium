#!/usr/bin/env python3
"""Scaffold a local personal/profile.json from the bundled template.

Refuses to overwrite an existing profile without --force -- a profile holds
real PII (CCCD, tax ID, contact details), so silent overwrite would be a
real data-loss risk, not just an inconvenience.

Usage:
    python init_profile.py <output_path> [--force]

Exit 0 = created, 1 = already exists (no --force), 2 = bad arguments.
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

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "profile_template.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_path", help="Where to write the new profile.json")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing file")
    args = parser.parse_args()

    out = Path(args.output_path)
    if out.exists() and not args.force:
        print(f"ERROR: {out} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    template_text = TEMPLATE.read_text(encoding="utf-8")
    # Round-trip through json to fail loudly if the bundled template itself is malformed.
    json.loads(template_text)
    out.write_text(template_text, encoding="utf-8", newline="\n")
    print(f"Created {out} from template. Edit it with your real details before use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
