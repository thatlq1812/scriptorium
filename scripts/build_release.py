#!/usr/bin/env python3
"""Package a raw release snapshot: skills/ + registry/ + START_HERE.md
(renamed to README.md inside the zip) into a single versioned .zip.

This is the "raw snapshot" release path START_HERE.md itself documents as
an alternative to skill-exporter's curated, gated bundle -- it ships
EVERYTHING in skills/registry as-is, with no license_debt/security_audit/
paused filtering. Use skill-exporter's export_bundle.py instead when a
curated, gated subset is what's actually needed; use this script when the
whole registry as one versioned drop is genuinely the goal (thatlq1812
decision, 2026-08-15, PROJECT.md release-design item).

Version comes from the repo-root VERSION file (YY.MM.NN scheme, bumped by
scripts/bump_version.ps1) -- never guessed, never re-derived here.

Usage:
    python scripts/build_release.py [-o releases/]

Output: <output_dir>/<VERSION>/scriptorium-<VERSION>.zip
Exit 0 = built, 1 = VERSION missing/malformed, 2 = skills/ or registry/
missing, 3 = output zip already exists (refuses to overwrite silently).
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VERSION_RE = re.compile(r"^\d{2}\.\d{2}\.\d+$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output-dir", default="releases", help="Base output directory (default: releases/).")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    version_file = root / "VERSION"
    skills_dir = root / "skills"
    registry_dir = root / "registry"
    start_here = root / "START_HERE.md"

    if not version_file.exists():
        print(f"ERROR: {version_file} not found.", file=sys.stderr)
        return 1
    version = version_file.read_text(encoding="utf-8").strip()
    if not VERSION_RE.match(version):
        print(f"ERROR: VERSION content {version!r} doesn't match the YY.MM.NN scheme.", file=sys.stderr)
        return 1

    for required in (skills_dir, registry_dir, start_here):
        if not required.exists():
            print(f"ERROR: required path missing: {required}", file=sys.stderr)
            return 2

    out_dir = root / args.output_dir / version
    zip_path = out_dir / f"scriptorium-{version}.zip"
    if zip_path.exists():
        print(f"ERROR: {zip_path} already exists -- refusing to overwrite. Bump VERSION first.", file=sys.stderr)
        return 3
    out_dir.mkdir(parents=True, exist_ok=True)

    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for base_dir, arc_prefix in ((skills_dir, "skills"), (registry_dir, "registry")):
            for path in sorted(base_dir.rglob("*")):
                if path.is_dir():
                    continue
                if "__pycache__" in path.parts:
                    continue
                arcname = f"{arc_prefix}/{path.relative_to(base_dir).as_posix()}"
                zf.write(path, arcname)
                file_count += 1
        zf.write(start_here, "README.md")
        file_count += 1

    print(f"Built {zip_path}")
    print(f"  version: {version}")
    print(f"  files: {file_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
