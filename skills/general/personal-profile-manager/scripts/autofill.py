#!/usr/bin/env python3
"""Auto-fill a target document's field values from a local profile.json.

This is a generic engine, same shape as legal-form-filler: the profile is
this skill's data, but WHICH target fields map to WHICH profile values is
always caller-supplied via a field_map.json (never hard-coded), since
Scriptorium has no built-in knowledge of any specific downstream form's
schema. A field_map entry whose dotted path doesn't resolve in the profile
is reported as unresolved, never silently dropped or invented -- the same
"never fabricate" discipline as every other skill in this registry.

field_map.json shape: { "target_field_name": "section.field", ... }
  e.g. { "ho_ten": "identity.full_name" }

Usage:
    python autofill.py <profile.json> <field_map.json> [-o filled.json]

Exit 0 = every mapped field resolved, 1 = at least one unresolved
(printed by name, output still written with resolved fields only if -o is
given -- caller must check the unresolved list before trusting it), 2 = malformed input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def _resolve_path(data: dict[str, Any], dotted_path: str) -> tuple[bool, Any]:
    """Resolve a dotted path like 'identity.full_name' against a nested dict.
    Returns (found, value). A non-string leaf or missing key both count as not found."""
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    if isinstance(current, (dict, list)):
        return False, None
    return True, current


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile_path")
    parser.add_argument("field_map_path")
    parser.add_argument("-o", "--output", help="Write resolved fields as JSON to this path")
    args = parser.parse_args()

    profile_path = Path(args.profile_path)
    field_map_path = Path(args.field_map_path)

    if not profile_path.exists():
        print(f"ERROR: profile not found: {profile_path}", file=sys.stderr)
        return 2
    if not field_map_path.exists():
        print(f"ERROR: field_map not found: {field_map_path}", file=sys.stderr)
        return 2

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {profile_path}: {e}", file=sys.stderr)
        return 2
    try:
        field_map = json.loads(field_map_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {field_map_path}: {e}", file=sys.stderr)
        return 2

    if not isinstance(profile, dict):
        print("ERROR: profile.json must be a JSON object.", file=sys.stderr)
        return 2
    if not isinstance(field_map, dict) or not field_map:
        print("ERROR: field_map.json must be a non-empty JSON object.", file=sys.stderr)
        return 2

    resolved: dict[str, Any] = {}
    unresolved: list[str] = []
    for target_field, dotted_path in field_map.items():
        if not isinstance(dotted_path, str) or not dotted_path.strip():
            unresolved.append(f"{target_field} -> (invalid path declaration: {dotted_path!r})")
            continue
        found, value = _resolve_path(profile, dotted_path)
        if found:
            resolved[target_field] = value
        else:
            unresolved.append(f"{target_field} -> {dotted_path} (not found in profile)")

    print(f"Resolved {len(resolved)}/{len(field_map)} field(s).")
    if unresolved:
        print("UNRESOLVED:", file=sys.stderr)
        for u in unresolved:
            print(f"  - {u}", file=sys.stderr)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(resolved, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        print(f"Wrote resolved fields to {out_path}")

    return 1 if unresolved else 0


if __name__ == "__main__":
    raise SystemExit(main())
