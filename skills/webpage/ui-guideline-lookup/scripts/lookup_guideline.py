#!/usr/bin/env python3
"""Deterministically look up real UI/UX Do/Don't guidelines by category,
platform, severity, and/or free-text keywords, from a bundled reference
of 151 curated entries -- 119 covering WEB (navigation, forms,
performance, typography...) and 32 covering MOBILE/APP interfaces (iOS/
Android/React Native touch targets, gestures, safe areas...). This is the
"broader than landing pages" companion to landing-page-composer: a
reference tool for reviewing ANY UI decision, not just page assembly.
Pure lookup, no AI/LLM call, no invented guidance. Stdlib only (json,
argparse), local, deterministic.

SCOPE LIMIT: this is a REFERENCE LOOKUP, not an automated code/design
checker -- it does not read your actual HTML/app code and detect
violations itself; it returns the relevant Do/Don't guidance for you (or
the calling agent) to apply during a real review.

Exit codes: 0 = match found, 1 = no match found, 2 = malformed input/args.

Usage:
    python lookup_guideline.py --category Accessibility --platform Web
    python lookup_guideline.py --keywords "touch target size"
    python lookup_guideline.py --severity Critical --platform "iOS/Android/React Native"
    python lookup_guideline.py --list-categories
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
VALID_SEVERITIES = {"Critical", "High", "Medium", "Low"}


def load_guidelines() -> list[dict]:
    path = REFERENCES_DIR / "guidelines.json"
    if not path.exists():
        sys.exit(f"ERROR: reference data file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--category", help="Exact category, e.g. 'Accessibility', 'Navigation', 'Forms'. See --list-categories.")
    parser.add_argument("--platform", help="Exact platform value, e.g. 'Web', 'All', 'iOS/Android/React Native'. See --list-platforms.")
    parser.add_argument("--severity", choices=sorted(VALID_SEVERITIES), help="Filter to this exact severity.")
    parser.add_argument("--keywords", help="Space-separated keywords, matched against issue/description text.")
    parser.add_argument("--list-categories", action="store_true", help="Print all distinct categories and exit.")
    parser.add_argument("--list-platforms", action="store_true", help="Print all distinct platform values and exit.")
    parser.add_argument("-o", "--output", type=Path, help="Write the result JSON to this file instead of stdout.")
    args = parser.parse_args()

    guidelines = load_guidelines()

    if args.list_categories:
        for cat in sorted({g["category"] for g in guidelines}):
            print(cat)
        return 0
    if args.list_platforms:
        for plat in sorted({g["platform"] for g in guidelines}):
            print(plat)
        return 0

    if not any([args.category, args.platform, args.severity, args.keywords]):
        print("ERROR: at least one filter (--category/--platform/--severity/--keywords) or a --list-* flag is required", file=sys.stderr)
        return 2

    results = guidelines
    if args.category:
        results = [g for g in results if g["category"].lower() == args.category.strip().lower()]
    if args.platform:
        results = [g for g in results if g["platform"].lower() == args.platform.strip().lower()]
    if args.severity:
        results = [g for g in results if g["severity"] == args.severity]
    if args.keywords:
        query_set = {k.strip().lower() for k in args.keywords.split() if k.strip()}
        results = [
            g for g in results
            if query_set & set((g["issue"] + " " + g["description"]).lower().split())
        ]

    if not results:
        print("NOT FOUND: no guideline matched the given filter(s). Try --list-categories/--list-platforms with fewer filters.", file=sys.stderr)
        return 1

    print(f"NOTE: {len(results)} guideline(s) matched -- this is reference material for you/the calling agent to apply, not an automated code check.", file=sys.stderr)
    output_text = json.dumps(results, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
        print(f"OK: wrote {args.output}")
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
