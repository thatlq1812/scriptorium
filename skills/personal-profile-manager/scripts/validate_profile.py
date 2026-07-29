#!/usr/bin/env python3
"""Validate a personal/profile.json against the required schema.

Required top-level sections: identity, organization, contact -- each a flat
object of string values. Refuses loudly (never silently accepts a partial
profile) so a later autofill run doesn't silently propagate missing data
into a real document.

Usage:
    python validate_profile.py <profile.json>

Exit 0 = valid, 1 = structural violations found (all printed), 2 = malformed JSON / missing file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_SECTIONS = {
    "identity": {"full_name"},
    "organization": {"org_name"},
    "contact": {"email"},
}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_profile.py <profile.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: profile file not found: {path}", file=sys.stderr)
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("ERROR: profile.json must be a JSON object at the top level.", file=sys.stderr)
        return 2

    errors: list[str] = []
    for section, required_fields in REQUIRED_SECTIONS.items():
        if section not in data:
            errors.append(f"missing required section: '{section}'")
            continue
        section_value = data[section]
        if not isinstance(section_value, dict):
            errors.append(f"section '{section}' must be an object, got {type(section_value).__name__}")
            continue
        for field in required_fields:
            value = section_value.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"section '{section}': required field '{field}' is missing or empty")

    if errors:
        print(f"INVALID ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"VALID: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
