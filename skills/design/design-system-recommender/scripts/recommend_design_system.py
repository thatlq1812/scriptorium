#!/usr/bin/env python3
"""Deterministically look up a curated design system (color tokens, a font
pairing, a recommended landing-page pattern) for a declared product/
industry type. Pure lookup + keyword-overlap scoring against a bundled,
curated reference dataset -- no AI/LLM call, no generation, no invented
values. Stdlib only (json, argparse, re), local, deterministic.

SCOPE LIMIT (read before use): this returns a CURATED RECOMMENDATION from
a real, pre-existing reference dataset (see references/PROVENANCE.md) --
it does not design anything new, does not adapt the palette to a specific
brand's actual logo/photos, and does not guarantee WCAG contrast for every
possible pairing of tokens beyond what the source dataset itself already
curated. Treat the result as a strong, real starting point, not a final,
unreviewed design decision.

Exit codes: 0 = found a match, 1 = no product_type/keyword match found,
2 = malformed input/args.

Usage:
    python recommend_design_system.py --product-type "SaaS (General)"
    python recommend_design_system.py --keywords "saas b2b cloud software"
    python recommend_design_system.py --list-product-types
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


def load_json(name: str) -> object:
    path = REFERENCES_DIR / name
    if not path.exists():
        sys.exit(f"ERROR: reference data file not found: {path} (this skill's references/ folder is required)")
    return json.loads(path.read_text(encoding="utf-8"))


def find_by_product_type(design_systems: list[dict], product_type: str) -> dict | None:
    for ds in design_systems:
        if ds["product_type"].strip().lower() == product_type.strip().lower():
            return ds
    return None


def find_by_keywords(design_systems: list[dict], query_keywords: list[str]) -> tuple[dict | None, int]:
    query_set = {k.strip().lower() for k in query_keywords if k.strip()}
    best_ds, best_score = None, 0
    for ds in design_systems:
        ds_keywords = {k.lower() for k in ds["keywords"]}
        score = len(query_set & ds_keywords)
        if score > best_score:
            best_ds, best_score = ds, score
    return best_ds, best_score


def best_font_pairing(font_pairings: list[dict], product_keywords: list[str]) -> dict | None:
    query_set = {k.strip().lower() for k in product_keywords if k.strip()}
    best_fp, best_score = None, -1
    for fp in font_pairings:
        mood_set = {k.lower() for k in fp["mood_keywords"]}
        best_for_text = fp["best_for"].lower()
        score = len(query_set & mood_set) + sum(1 for k in query_set if k in best_for_text)
        if score > best_score:
            best_fp, best_score = fp, score
    return best_fp


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--product-type", help="Exact product-type name, e.g. 'SaaS (General)'. See --list-product-types.")
    parser.add_argument("--keywords", help="Space-separated keywords to fuzzy-match against, e.g. 'saas b2b cloud'")
    parser.add_argument("--list-product-types", action="store_true", help="Print all recognized product_type values and exit.")
    parser.add_argument("-o", "--output", type=Path, help="Write the result JSON to this file instead of stdout.")
    args = parser.parse_args()

    design_systems = load_json("design_systems.json")
    font_pairings = load_json("font_pairings.json")

    if args.list_product_types:
        for ds in design_systems:
            print(ds["product_type"])
        return 0

    if not args.product_type and not args.keywords:
        print("ERROR: one of --product-type, --keywords, or --list-product-types is required", file=sys.stderr)
        return 2

    ds = None
    if args.product_type:
        ds = find_by_product_type(design_systems, args.product_type)
        if ds is None:
            print(f"NOT FOUND: no exact product_type match for {args.product_type!r}. Try --keywords or --list-product-types.", file=sys.stderr)
            return 1
    else:
        ds, score = find_by_keywords(design_systems, args.keywords.split())
        if ds is None or score == 0:
            print(f"NOT FOUND: no keyword overlap found for {args.keywords!r}. Try --list-product-types.", file=sys.stderr)
            return 1
        print(f"NOTE: matched product_type {ds['product_type']!r} via {score} overlapping keyword(s) -- review before trusting blindly.", file=sys.stderr)

    fp = best_font_pairing(font_pairings, ds["keywords"])

    result = {
        "product_type": ds["product_type"],
        "primary_style_recommendation": ds["primary_style_recommendation"],
        "color_tokens": ds["color_tokens"],
        "color_notes": ds["color_notes"],
        "font_pairing": {
            "name": fp["name"],
            "heading_font": fp["heading_font"],
            "body_font": fp["body_font"],
            "google_fonts_url": fp["google_fonts_url"],
        } if fp else None,
        "landing_pattern_name": ds["landing_pattern_name"],
        "landing_pattern_id": ds["landing_pattern_id"],
        "landing_section_order": ds["landing_section_order"],
        "key_considerations": ds["key_considerations"],
    }

    output_text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
        print(f"OK: wrote {args.output}")
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
