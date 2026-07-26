#!/usr/bin/env python3
"""Check a provided-documents list against a required-documents checklist
for a legal/administrative procedure. Stdlib only (json, argparse), local,
deterministic -- no AI/network call of any kind.

The checklist itself is ALWAYS caller-supplied, never hard-coded: this
project has no real government-procedure checklist data to bake in (unlike
lesson-plan-builder's CV5512 structure, which is a fixed national
standard), so this script is a generic completeness-checking engine, not a
specific procedure's rules.

Matching is case/whitespace-normalized exact string match -- deliberately
not fuzzy, since a fuzzy match on "which documents were actually provided"
is exactly the kind of judgment call that shouldn't be silently automated
in a legal-procedure context. A near-miss is reported as missing, not
guessed to be a match.

Exit codes: 0 = complete, 1 = missing documents found, 2 = malformed input.

Usage:
    python check_dossier.py checklist.json provided.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


class DossierError(Exception):
    pass


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


def load_list(path: Path, key: str) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DossierError(f"cannot read {path.name}: {exc}") from exc
    items = data.get(key) if isinstance(data, dict) else None
    if not isinstance(items, list) or not items or not all(isinstance(x, str) and x.strip() for x in items):
        raise DossierError(f"{path.name} must be an object with a non-empty '{key}' list of non-empty strings")
    return items


def check(required: list[str], provided: list[str]) -> tuple[list[str], list[str]]:
    provided_normalized = {_normalize(p) for p in provided}
    missing = [r for r in required if _normalize(r) not in provided_normalized]
    required_normalized = {_normalize(r) for r in required}
    extra = [p for p in provided if _normalize(p) not in required_normalized]
    return missing, extra


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("checklist", type=Path, help="Path to a checklist JSON file (see assets/checklist_template.json)")
    parser.add_argument("provided", type=Path, help="Path to a provided-documents JSON file (see assets/provided_documents_template.json)")
    args = parser.parse_args()

    try:
        required = load_list(args.checklist, "required_documents")
        provided = load_list(args.provided, "documents_provided")
    except DossierError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    missing, extra = check(required, provided)

    if extra:
        print(f"NOTE: {len(extra)} provided document(s) don't match any checklist entry (not necessarily a problem, just informational):")
        for e in extra:
            print(f"  - {e}")

    if missing:
        print(f"INCOMPLETE: {len(missing)} of {len(required)} required document(s) missing:")
        for m in missing:
            print(f"  - {m}")
        return 1

    print(f"OK: all {len(required)} required document(s) present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
