#!/usr/bin/env python3
"""Check that a legal term was translated the same way every time it was
used, against a fixed glossary (references/legal-glossary.json). Stdlib
only (json, argparse), local, deterministic -- no AI/network call.

This does NOT translate anything itself and does NOT scan free text for
term usage (matching whether "Indemnification" appears in a document is a
judgment call the translator/agent already made) -- it validates a usage
log the translator/agent already recorded: for every logged instance of a
glossary term, was the translation the registered one (or an approved
alias), and is the SAME term translated the same way everywhere it was
logged. Same discipline as legal-citation-checker's title-consistency
check and contract-consistency-linter's party-label check, applied to
terminology instead.

Exit codes: 0 = consistent, 1 = inconsistency found, 2 = malformed input.

Usage:
    python check_terminology_consistency.py <usage_log.json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

GLOSSARY_PATH = Path(__file__).resolve().parents[1] / "references" / "legal-glossary.json"


def load_glossary() -> dict[str, dict]:
    data = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
    return {t["id"]: t for t in data["terms"]}


def validate(entries: list[dict], glossary: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    used_translations: dict[str, set[str]] = {}

    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            errors.append(f"entries[{i}] must be an object")
            continue
        term_id = e.get("term_id")
        translated_as = e.get("translated_as")
        if not term_id:
            errors.append(f"entries[{i}]: term_id is required")
            continue
        if not translated_as:
            errors.append(f"entries[{i}] ({term_id}): translated_as is required")
            continue

        term = glossary.get(term_id)
        if term is None:
            known = sorted(glossary)
            errors.append(f"entries[{i}]: term_id {term_id!r} is not in the glossary -- likely a typo. Known: {known}")
            continue

        allowed = {term["vi"], *term.get("aliases_vi", [])}
        if translated_as not in allowed:
            errors.append(
                f"entries[{i}] ({term_id}): translated as {translated_as!r}, but the glossary registers "
                f"{term['vi']!r} (aliases: {term.get('aliases_vi', [])}) -- not a registered translation for this term"
            )
            continue

        used_translations.setdefault(term_id, set()).add(translated_as)

    for term_id, translations in used_translations.items():
        if len(translations) > 1:
            errors.append(
                f"term_id {term_id!r} translated inconsistently across entries: {sorted(translations)} -- "
                f"even though all are registered (glossary term + aliases), verify this is intentional, not accidental"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("usage_log", type=Path, help="Path to a usage-log JSON file (see assets/usage_log_template.json)")
    args = parser.parse_args()

    if not args.usage_log.exists():
        print(f"Input not found: {args.usage_log}", file=sys.stderr)
        return 1

    try:
        data = json.loads(args.usage_log.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list) or not entries:
        print("MALFORMED: input must be an object with a non-empty 'entries' list", file=sys.stderr)
        return 2

    glossary = load_glossary()
    errors = validate(entries, glossary)

    if errors:
        print(f"INCONSISTENT: {len(errors)} issue(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {len(entries)} term usage(s) checked, all consistent with the glossary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
