#!/usr/bin/env python3
"""Deterministically recommend a UI icon by keyword or exact name from a
bundled, curated 105-icon Phosphor catalog -- returns the real import
code and, critically, the correct accessibility treatment (decorative vs.
meaningful vs. interactive, per the icon's real allowed semantic roles).
Pure lookup, no AI/LLM call, no invented icon. Stdlib only (json,
argparse), local, deterministic.

SCOPE LIMIT: recommends from a REAL, PRE-EXISTING curated 105-icon subset
of the Phosphor icon library (not the full ~1,500+ real Phosphor set) --
if no good match exists in this subset, that is disclosed as a real
not-found, never papered over with a close-but-wrong recommendation.

Exit codes: 0 = match found, 1 = no match found, 2 = malformed input/args.

Usage:
    python recommend_icon.py --icon-name arrow-left
    python recommend_icon.py --keywords "delete remove trash"
    python recommend_icon.py --category Navigation
    python recommend_icon.py --list-categories
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"


def load_icons() -> list[dict]:
    path = REFERENCES_DIR / "icons.json"
    if not path.exists():
        sys.exit(f"ERROR: reference data file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def find_by_name(icons: list[dict], name: str) -> dict | None:
    target = name.strip().lower()
    for i in icons:
        if i["icon_name"].lower() == target:
            return i
    return None


def find_by_keywords(icons: list[dict], query_keywords: list[str]) -> list[tuple[dict, int]]:
    query_set = {k.strip().lower() for k in query_keywords if k.strip()}
    scored = []
    for i in icons:
        icon_set = {k.lower() for k in i["keywords"]} | {i["icon_name"].lower()}
        score = len(query_set & icon_set)
        if score > 0:
            scored.append((i, score))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--icon-name", help="Exact icon name, e.g. 'arrow-left'.")
    parser.add_argument("--keywords", help="Space-separated keywords to fuzzy-match, e.g. 'delete remove trash'")
    parser.add_argument("--category", help="List every icon in this exact category, e.g. 'Navigation'.")
    parser.add_argument("--list-categories", action="store_true", help="Print all distinct categories and exit.")
    parser.add_argument("--max-results", type=int, default=3, help="Max results for --keywords (default 3)")
    parser.add_argument("-o", "--output", type=Path, help="Write the result JSON to this file instead of stdout.")
    args = parser.parse_args()

    icons = load_icons()

    if args.list_categories:
        for cat in sorted({i["category"] for i in icons}):
            print(cat)
        return 0

    if not any([args.icon_name, args.keywords, args.category]):
        print("ERROR: one of --icon-name, --keywords, --category, or --list-categories is required", file=sys.stderr)
        return 2

    result: object
    if args.icon_name:
        found = find_by_name(icons, args.icon_name)
        if found is None:
            print(f"NOT FOUND: no exact icon_name match for {args.icon_name!r}. Try --keywords or --list-categories.", file=sys.stderr)
            return 1
        result = found
    elif args.category:
        matches = [i for i in icons if i["category"].lower() == args.category.strip().lower()]
        if not matches:
            print(f"NOT FOUND: no icons in category {args.category!r}. Try --list-categories.", file=sys.stderr)
            return 1
        result = matches
    else:
        scored = find_by_keywords(icons, args.keywords.split())
        if not scored:
            print(f"NOT FOUND: no keyword overlap found for {args.keywords!r}.", file=sys.stderr)
            return 1
        top = scored[: args.max_results]
        print(f"NOTE: {len(top)} candidate(s) found, best overlap score {top[0][1]} -- review before trusting blindly.", file=sys.stderr)
        result = [icon for icon, _score in top]

    output_text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
        print(f"OK: wrote {args.output}")
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
