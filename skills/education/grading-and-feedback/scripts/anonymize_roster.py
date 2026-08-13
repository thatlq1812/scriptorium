#!/usr/bin/env python3
"""LOCAL-ONLY roster anonymization helper — stdlib only, no network, no
LLM call. Two modes:

  anonymize  — given a list of real student names, deterministically
               assigns stable anonymous codes (HS01, HS02, ... in list
               order — the SAME input order always produces the SAME
               codes) and writes a local mapping file.
  reattach   — given a results file keyed by those anonymous codes and
               the same local mapping file, re-attaches real names to a
               new output file. Never touches the network.

SENSITIVE / LOCAL-ONLY: the mapping file this writes (roster_map.json by
default) contains the real HSnn <-> real-name correspondence. Per Vietnam's
Quy chế AI Điều 6 (student PII data-sensitivity rule), this file must never
be sent to an LLM/network call or leave local storage — only `anonymize`
and `reattach` in this script read it, and both run entirely offline.

Usage:
    python anonymize_roster.py anonymize <roster.json> --out roster_map.json
    python anonymize_roster.py reattach <results.json> <roster_map.json> --out results_named.json

roster.json shape (see assets/roster_template.json):
    { "students": [ { "full_name": "<real name>" }, ... ] }

results.json for reattach: any JSON document. Every string value found in
it (recursively, in dict values, list items, and dict/list keys) that
exactly equals a mapped anonymous code is replaced with the real name. The
document structure is otherwise preserved unchanged.

Exit codes: 0 = success, 1 = refused (e.g. output already exists without
--force, code in results.json not found in the mapping), 2 = malformed
input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def _load_json(path: Path, label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SystemExit(f"MALFORMED {label}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"MALFORMED {label}: top-level JSON must be an object")
    return data


def build_codes(n: int) -> list[str]:
    """HS01, HS02, ... HS99, HS100, ... — always zero-padded to at least 2
    digits, deterministic and stable for a given roster order/length."""
    width = max(2, len(str(n)))
    return [f"HS{str(i).zfill(width)}" for i in range(1, n + 1)]


def cmd_anonymize(args: argparse.Namespace) -> int:
    roster = _load_json(args.roster, "roster")
    students = roster.get("students")
    if not isinstance(students, list) or not students:
        print("MALFORMED roster: 'students' must be a non-empty list", file=sys.stderr)
        return 2

    names: list[str] = []
    for i, entry in enumerate(students):
        if not isinstance(entry, dict):
            print(f"MALFORMED roster: students[{i}] must be an object", file=sys.stderr)
            return 2
        name = str(entry.get("full_name", "")).strip()
        if not name:
            print(f"MALFORMED roster: students[{i}] missing 'full_name'", file=sys.stderr)
            return 2
        names.append(name)

    codes = build_codes(len(names))
    mapping = {
        "_sensitive": "LOCAL-ONLY. Do not send this file's contents to any LLM/network call. See Quy che AI Dieu 6.",
        "students": [{"code": code, "full_name": name} for code, name in zip(codes, names)],
    }

    if args.out.exists() and not args.force:
        print(f"REFUSED: {args.out} already exists, use --force to overwrite", file=sys.stderr)
        return 1

    args.out.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: wrote {args.out} ({len(names)} student(s) mapped)")
    for entry in mapping["students"]:
        print(f"  - {entry['code']}")
    return 0


def _load_mapping(path: Path) -> dict[str, str]:
    data = _load_json(path, "roster_map")
    students = data.get("students")
    if not isinstance(students, list) or not students:
        raise SystemExit("MALFORMED roster_map: 'students' must be a non-empty list")
    code_to_name: dict[str, str] = {}
    for i, entry in enumerate(students):
        if not isinstance(entry, dict):
            raise SystemExit(f"MALFORMED roster_map: students[{i}] must be an object")
        code = str(entry.get("code", "")).strip()
        name = str(entry.get("full_name", "")).strip()
        if not code or not name:
            raise SystemExit(f"MALFORMED roster_map: students[{i}] missing 'code' or 'full_name'")
        if code in code_to_name:
            raise SystemExit(f"MALFORMED roster_map: duplicate code {code!r}")
        code_to_name[code] = name
    return code_to_name


def _reattach_value(value: object, mapping: dict[str, str], unmapped: set[str]) -> object:
    if isinstance(value, str):
        if value in mapping:
            return mapping[value]
        return value
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            new_key = mapping.get(k, k)
            out[new_key] = _reattach_value(v, mapping, unmapped)
        return out
    if isinstance(value, list):
        return [_reattach_value(v, mapping, unmapped) for v in value]
    return value


def _find_codes(value: object, mapping: dict[str, str], found: set[str]) -> None:
    if isinstance(value, str):
        if value in mapping:
            found.add(value)
    elif isinstance(value, dict):
        for k, v in value.items():
            if k in mapping:
                found.add(k)
            _find_codes(v, mapping, found)
    elif isinstance(value, list):
        for v in value:
            _find_codes(v, mapping, found)


def cmd_reattach(args: argparse.Namespace) -> int:
    mapping = _load_mapping(args.roster_map)
    results = _load_json(args.results, "results")

    found: set[str] = set()
    _find_codes(results, mapping, found)
    if not found:
        print("REFUSED: no anonymous code from roster_map was found anywhere in results — nothing to reattach", file=sys.stderr)
        return 1

    unmapped: set[str] = set()
    reattached = _reattach_value(results, mapping, unmapped)

    if args.out.exists() and not args.force:
        print(f"REFUSED: {args.out} already exists, use --force to overwrite", file=sys.stderr)
        return 1

    args.out.write_text(json.dumps(reattached, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: wrote {args.out} ({len(found)} code(s) reattached: {sorted(found)})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)

    p_anon = sub.add_parser("anonymize", help="Assign HSnn codes to a real-name roster and write a local mapping file")
    p_anon.add_argument("roster", type=Path, help="Path to a roster JSON file (see assets/roster_template.json)")
    p_anon.add_argument("--out", type=Path, default=Path("roster_map.json"), help="Output mapping file path (default roster_map.json) -- SENSITIVE, local-only")
    p_anon.add_argument("--force", action="store_true")
    p_anon.set_defaults(func=cmd_anonymize)

    p_re = sub.add_parser("reattach", help="Re-attach real names to a results file using a local mapping file")
    p_re.add_argument("results", type=Path, help="Path to a results JSON file keyed by HSnn codes")
    p_re.add_argument("roster_map", type=Path, help="Path to the local mapping file produced by 'anonymize'")
    p_re.add_argument("--out", type=Path, required=True, help="Output file path with real names reattached")
    p_re.add_argument("--force", action="store_true")
    p_re.set_defaults(func=cmd_reattach)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
