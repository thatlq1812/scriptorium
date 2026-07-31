#!/usr/bin/env python3
"""Deterministic brand-identity asset-completeness checklist.

Given a caller-declared list of asset-type keys already produced (e.g.
"logo-icon", "banner-hero"), reports which required deliverables from the
standard brand-identity checklist are still missing. Pure gap-report --
no image generation, no file creation, no network calls.

The checklist (8 required core assets + 7 derived/auto-generated variants)
is grounded in a real production brand-asset generation pipeline's own
asset manifest (D:/elix/archive/platform_archive/scripts/gen/
gen_brand_identity.py and gen_brand_icon.py) -- specifically the set of
deliverables it produces, not its AI-image-generation mechanism (which is
out of scope for this deterministic utility; see SKILL.md).

Usage:
    python check_asset_completeness.py <declared_assets.json>

Exit 0 = all required assets declared (checklist complete), 1 = one or
more required assets missing (listed by name), 2 = malformed input
(not valid JSON, wrong shape, or an unrecognized asset-type key that
cannot be checked against the checklist at all).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

CHECKLIST_PATH = Path(__file__).parent.parent / "assets" / "asset_checklist.json"


def _load_checklist() -> tuple[list[str], list[str]]:
    data = json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))
    required = [item["key"] for item in data["required"]]
    derived = [item["key"] for item in data["derived"]]
    return required, derived


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python check_asset_completeness.py <declared_assets.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        return 2

    if not isinstance(data, dict) or "declared_assets" not in data:
        print("ERROR: input must be an object with key 'declared_assets' (a list of asset-type keys)", file=sys.stderr)
        return 2

    declared = data["declared_assets"]
    if not isinstance(declared, list) or not all(isinstance(x, str) for x in declared):
        print("ERROR: 'declared_assets' must be a list of strings", file=sys.stderr)
        return 2

    required, derived = _load_checklist()
    known = set(required) | set(derived)

    unrecognized = sorted({a for a in declared if a not in known})
    if unrecognized:
        print(
            f"ERROR: {len(unrecognized)} declared asset-type key(s) not recognized by the checklist: "
            f"{unrecognized}. Recognized required keys: {sorted(required)}. "
            f"Recognized derived keys: {sorted(derived)}.",
            file=sys.stderr,
        )
        return 2

    declared_set = set(declared)
    missing = [key for key in required if key not in declared_set]
    missing_derived = [key for key in derived if key not in declared_set]

    if missing:
        print(f"MISSING: {len(missing)} required asset(s) not yet declared:")
        for key in missing:
            print(f"  - {key}")
        if missing_derived:
            print(f"INFO: {len(missing_derived)} derived asset(s) also not declared (not required):")
            for key in missing_derived:
                print(f"  - {key}")
        return 1

    print(f"COMPLETE: all {len(required)} required assets declared.")
    if missing_derived:
        print(f"INFO: {len(missing_derived)} derived asset(s) not declared (not required):")
        for key in missing_derived:
            print(f"  - {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
