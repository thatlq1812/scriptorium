#!/usr/bin/env python3
"""Deterministically look up a curated UI visual style (Glassmorphism,
Neumorphism, Brutalism, Bento Grid, etc.) by exact style_id or free-text
keywords, returning its real CSS implementation guidance -- colors,
effects, an implementation checklist, CSS custom-property variables,
accessibility risk notes, and framework compatibility. Pure lookup from a
bundled, curated reference dataset (88 real styles) -- no AI/LLM call, no
invented styling advice. Stdlib only (json, argparse), local,
deterministic.

SCOPE LIMIT: this returns a CURATED REFERENCE ENTRY, never a generated or
brand-new style. It does not verify WCAG contrast for a specific real
color combination beyond the source dataset's own accessibility risk
notes -- treat the "accessibility" field as a starting risk signal, not a
pass/fail audit.

Exit codes: 0 = match found, 1 = no match found, 2 = malformed input/args.

Usage:
    python lookup_style.py --style-id glassmorphism
    python lookup_style.py --keywords "soft rounded pastel"
    python lookup_style.py --list-styles
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


def load_styles() -> list[dict]:
    path = REFERENCES_DIR / "styles.json"
    if not path.exists():
        sys.exit(f"ERROR: reference data file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def find_by_id(styles: list[dict], style_id: str) -> dict | None:
    target = style_id.strip().lower()
    for s in styles:
        if s["style_id"].lower() == target:
            return s
    return None


def find_by_keywords(styles: list[dict], query_keywords: list[str]) -> tuple[dict | None, int]:
    query_set = {k.strip().lower() for k in query_keywords if k.strip()}
    best, best_score = None, 0
    for s in styles:
        style_set = {k.lower() for k in s["keywords"]}
        score = len(query_set & style_set)
        if score > best_score:
            best, best_score = s, score
    return best, best_score


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--style-id", help="Exact style id, e.g. 'glassmorphism'. See --list-styles.")
    parser.add_argument("--keywords", help="Space-separated keywords to fuzzy-match, e.g. 'soft rounded pastel'")
    parser.add_argument("--list-styles", action="store_true", help="Print all style_id + style_category values and exit.")
    parser.add_argument("-o", "--output", type=Path, help="Write the result JSON to this file instead of stdout.")
    args = parser.parse_args()

    styles = load_styles()

    if args.list_styles:
        for s in styles:
            print(f"{s['style_id']}\t{s['style_category']}")
        return 0

    if not args.style_id and not args.keywords:
        print("ERROR: one of --style-id, --keywords, or --list-styles is required", file=sys.stderr)
        return 2

    if args.style_id:
        result = find_by_id(styles, args.style_id)
        if result is None:
            print(f"NOT FOUND: no exact style_id match for {args.style_id!r}. Try --keywords or --list-styles.", file=sys.stderr)
            return 1
    else:
        result, score = find_by_keywords(styles, args.keywords.split())
        if result is None or score == 0:
            print(f"NOT FOUND: no keyword overlap found for {args.keywords!r}. Try --list-styles.", file=sys.stderr)
            return 1
        print(f"NOTE: matched style_id {result['style_id']!r} via {score} overlapping keyword(s) -- review before trusting blindly.", file=sys.stderr)

    output_text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
        print(f"OK: wrote {args.output}")
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
