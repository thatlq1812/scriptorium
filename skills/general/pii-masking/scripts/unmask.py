#!/usr/bin/env python3
"""Re-attach real sensitive values to a masked file using the LOCAL-ONLY
mapping file produced by mask_terms.py. Never touches the network.

Usage:
    python unmask.py <masked_file> <map.json> --out unmasked.md [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def load_mapping(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED map.json: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict) or not isinstance(data.get("terms"), list) or not data["terms"]:
        print("MALFORMED map.json: must be an object with a non-empty 'terms' array.", file=sys.stderr)
        raise SystemExit(2)
    code_to_value: dict[str, str] = {}
    for i, entry in enumerate(data["terms"]):
        if not isinstance(entry, dict):
            print(f"MALFORMED map.json: terms[{i}] must be an object", file=sys.stderr)
            raise SystemExit(2)
        code = str(entry.get("code", "")).strip()
        value = str(entry.get("value", ""))
        if not code or not value:
            print(f"MALFORMED map.json: terms[{i}] missing 'code' or 'value'", file=sys.stderr)
            raise SystemExit(2)
        if code in code_to_value:
            print(f"MALFORMED map.json: duplicate code {code!r}", file=sys.stderr)
            raise SystemExit(2)
        code_to_value[code] = value
    return code_to_value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("masked_file", type=Path)
    parser.add_argument("map_json", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.masked_file.exists():
        print(f"Input not found: {args.masked_file}", file=sys.stderr)
        return 1
    if not args.map_json.exists():
        print(f"map.json not found: {args.map_json}", file=sys.stderr)
        return 1
    if args.out.exists() and not args.force:
        print(f"REFUSED: {args.out} already exists, use --force to overwrite", file=sys.stderr)
        return 2

    mapping = load_mapping(args.map_json)
    text = args.masked_file.read_text(encoding="utf-8")

    found: set[str] = set()
    unmasked = text
    for code, value in mapping.items():
        if code in unmasked:
            found.add(code)
            unmasked = unmasked.replace(code, value)

    if not found:
        print("REFUSED: no placeholder code from map.json was found anywhere in the input -- nothing to unmask", file=sys.stderr)
        return 1

    args.out.write_text(unmasked, encoding="utf-8", newline="\n")
    missing = sorted(set(mapping) - found)
    print(f"OK: wrote {args.out} ({len(found)} code(s) reattached)")
    if missing:
        print(f"NOTE: {len(missing)} code(s) from map.json were not present in the input (not necessarily an error, e.g. partial excerpt): {missing}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
