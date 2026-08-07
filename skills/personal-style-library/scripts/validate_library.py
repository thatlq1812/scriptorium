#!/usr/bin/env python3
"""Deterministic validator for a personal style-library directory (4
categories: palettes, styles, motifs, fonts). No AI call, no network.

Reuses two other skills' own validation logic directly (cross-skill import,
same pattern poster-generator already uses for svg-poster-builder) instead
of duplicating it:
  - palettes/*.json: colors block validated via brand-identity-linter's
    own resolve_colors() -- same primary/secondary/accent/background
    fallback-chain rules, so a palette entry that passes here is guaranteed
    to also pass brand-identity-linter unchanged.
  - styles/*.json: description/reference_images/strength block validated
    via media-anchor-profile's own _validate_anchor_block() -- same rules
    a "style" block inside an anchor profile must satisfy, so a style entry
    that passes here is guaranteed to export cleanly (see
    export_anchor_profile.py).

motifs/*.json and fonts/*.json have no other skill's schema to reuse --
validated directly here (grounded in brand-identity-linter's own 'motifs'
field shape and light-logo-arranger's font-pairing concept respectively,
see SKILL.md).

Usage:
    python validate_library.py <library_root> [--category palettes|styles|motifs|fonts]

<library_root> is a style_library/ directory (see init_library.py).

Exit 0 = every entry found is valid (prints a per-category count), 1 = one
or more entries invalid -- including malformed JSON in a specific entry
file, reported alongside any other issues rather than aborting the whole
run (all errors printed, not just the first) -- or a required sibling
skill (brand-identity-linter / media-anchor-profile) isn't installed, 2 =
library_root itself doesn't exist (unrecoverable before any entry can be
checked).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

CATEGORIES = ("palettes", "styles", "motifs", "fonts")

_SCRIPTS_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _SCRIPTS_DIR.parents[1]

sys.path.insert(0, str(_SKILLS_ROOT / "brand-identity-linter" / "scripts"))
try:
    from validate_brand import resolve_colors  # noqa: E402
except ImportError:
    sys.exit(
        "validate_library.py requires the 'brand-identity-linter' skill installed as a "
        "sibling skill folder -- it reuses that skill's own color-role resolution logic "
        "for the 'palettes' category rather than duplicating it."
    )

sys.path.insert(0, str(_SKILLS_ROOT / "media-anchor-profile" / "scripts"))
try:
    from validate_profile import _validate_anchor_block  # noqa: E402
except ImportError:
    sys.exit(
        "validate_library.py requires the 'media-anchor-profile' skill installed as a "
        "sibling skill folder -- it reuses that skill's own anchor-block validation logic "
        "for the 'styles' category rather than duplicating it."
    )

STRENGTH_LEVELS = ("strict", "moderate", "loose")


def _validate_palette(entry: dict) -> list[str]:
    errors: list[str] = []
    palette_id = entry.get("palette_id")
    if not isinstance(palette_id, str) or not palette_id.strip():
        errors.append("'palette_id' is required and must be a non-empty string")
    resolve_colors(entry.get("colors"), errors)  # appends into errors, same contract as brand-identity-linter
    unknown = set(entry.keys()) - {"palette_id", "colors", "source", "source_image", "notes"}
    if unknown:
        errors.append(f"unknown top-level key(s): {sorted(unknown)}")
    if entry.get("source") == "extracted_from_image" and not entry.get("source_image"):
        errors.append("'source' is 'extracted_from_image' but 'source_image' is missing")
    return errors


def _validate_style(entry: dict, base_dir: Path) -> list[str]:
    errors: list[str] = []
    style_id = entry.get("style_id")
    if not isinstance(style_id, str) or not style_id.strip():
        errors.append("'style_id' is required and must be a non-empty string")
    block = {k: v for k, v in entry.items() if k != "style_id"}
    errors.extend(_validate_anchor_block("style", block, base_dir))
    return errors


def _validate_motif_set(entry: dict) -> list[str]:
    errors: list[str] = []
    motif_set_id = entry.get("motif_set_id")
    if not isinstance(motif_set_id, str) or not motif_set_id.strip():
        errors.append("'motif_set_id' is required and must be a non-empty string")
    motifs = entry.get("motifs")
    if not isinstance(motifs, list) or not motifs or not all(isinstance(m, str) and m.strip() for m in motifs):
        errors.append("'motifs' must be a non-empty list of non-empty strings")
    unknown = set(entry.keys()) - {"motif_set_id", "motifs", "notes"}
    if unknown:
        errors.append(f"unknown top-level key(s): {sorted(unknown)}")
    return errors


def _validate_font_pairing(entry: dict) -> list[str]:
    errors: list[str] = []
    font_pairing_id = entry.get("font_pairing_id")
    if not isinstance(font_pairing_id, str) or not font_pairing_id.strip():
        errors.append("'font_pairing_id' is required and must be a non-empty string")
    for field in ("heading_font", "body_font"):
        val = entry.get(field)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"'{field}' is required and must be a non-empty string")
    unknown = set(entry.keys()) - {"font_pairing_id", "heading_font", "body_font", "notes"}
    if unknown:
        errors.append(f"unknown top-level key(s): {sorted(unknown)}")
    return errors


_VALIDATORS = {
    "palettes": lambda entry, path: _validate_palette(entry),
    "styles": lambda entry, path: _validate_style(entry, path.parent),
    "motifs": lambda entry, path: _validate_motif_set(entry),
    "fonts": lambda entry, path: _validate_font_pairing(entry),
}


def validate_category(library_root: Path, category: str) -> tuple[int, list[str]]:
    """Returns (valid_count, all_errors) for every *.json file directly under
    library_root/category/. all_errors entries are prefixed with the file path."""
    category_dir = library_root / category
    if not category_dir.is_dir():
        return 0, []

    valid_count = 0
    all_errors: list[str] = []
    for entry_path in sorted(category_dir.glob("*.json")):
        try:
            entry = json.loads(entry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            all_errors.append(f"{entry_path}: malformed JSON: {e}")
            continue
        if not isinstance(entry, dict):
            all_errors.append(f"{entry_path}: must be a JSON object")
            continue
        entry_errors = _VALIDATORS[category](entry, entry_path)
        if entry_errors:
            all_errors.extend(f"{entry_path}: {e}" for e in entry_errors)
        else:
            valid_count += 1
    return valid_count, all_errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("library_root")
    parser.add_argument("--category", choices=CATEGORIES, help="Validate only this category (default: all 4).")
    args = parser.parse_args()

    library_root = Path(args.library_root)
    if not library_root.is_dir():
        print(f"ERROR: library_root not found or not a directory: {library_root}", file=sys.stderr)
        return 2

    categories = [args.category] if args.category else list(CATEGORIES)
    total_valid = 0
    all_errors: list[str] = []
    counts: dict[str, int] = {}
    for category in categories:
        valid_count, errors = validate_category(library_root, category)
        counts[category] = valid_count
        total_valid += valid_count
        all_errors.extend(errors)

    if all_errors:
        print(f"INVALID ({len(all_errors)} issue(s) across {len(categories)} categor{'y' if len(categories)==1 else 'ies'}):", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"VALID: {library_root}")
    for category in categories:
        print(f"  {category}: {counts[category]} entr{'y' if counts[category]==1 else 'ies'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
