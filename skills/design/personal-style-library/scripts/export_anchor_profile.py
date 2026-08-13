#!/usr/bin/env python3
"""Compose a styles/<name>.json library entry into a valid
media-anchor-profile anchor-profile JSON, ready for gemini-generator
(or any other media-anchor-profile consumer) to use for one generation call.

The output is validated via media-anchor-profile's OWN validate_anchor_profile()
before being written -- never assumed valid just because the source library
entry passed validate_library.py (the shapes are close but not identical:
a library entry has a top-level style_id, an anchor profile has a top-level
profile_id + nested 'style' block).

Usage:
    python export_anchor_profile.py <styles/name.json> <profile_id> -o anchor_profile.json

Exit 0 = exported, 1 = the composed profile failed media-anchor-profile's
own validator (all errors printed -- should only happen if the source style
entry references reference_images that moved since it was validated) OR
media-anchor-profile isn't installed as a sibling skill, 2 = malformed
input/args (bad JSON, missing style_id, empty profile_id).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

_SKILLS_ROOT = Path(__file__).resolve().parents[3]
_media_anchor_profile = next(_SKILLS_ROOT.glob("*/media-anchor-profile"), None)
if _media_anchor_profile is None:
    sys.exit(
        "export_anchor_profile.py requires the 'media-anchor-profile' skill installed as a "
        "sibling skill folder -- the exported profile is validated against that skill's own "
        "validator before being written, never assumed valid."
    )
sys.path.insert(0, str(_media_anchor_profile / "scripts"))
from validate_profile import validate_anchor_profile  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("style_entry_path")
    parser.add_argument("profile_id")
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    style_path = Path(args.style_entry_path)
    if not style_path.exists():
        print(f"ERROR: style entry not found: {style_path}", file=sys.stderr)
        return 2
    try:
        style_entry = json.loads(style_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {style_path}: {e}", file=sys.stderr)
        return 2
    if not isinstance(style_entry, dict) or "style_id" not in style_entry:
        print(f"ERROR: {style_path} is not a valid style library entry (missing 'style_id').", file=sys.stderr)
        return 2

    if not args.profile_id.strip():
        print("ERROR: profile_id must be a non-empty string.", file=sys.stderr)
        return 2

    style_block = {k: v for k, v in style_entry.items() if k != "style_id"}
    profile = {"profile_id": args.profile_id, "style": style_block}

    errors = validate_anchor_profile(profile, base_dir=style_path.parent)
    if errors:
        print(f"INVALID composed profile ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(profile, indent=2), encoding="utf-8", newline="\n")
    print(f"Exported {style_path} -> {out_path} (profile_id={args.profile_id!r}, media-anchor-profile-valid)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
