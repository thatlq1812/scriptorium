#!/usr/bin/env python3
"""Deterministic font-fallback resolver for wordmark/logo-placement text.

Given a caller-declared font name, reports whether it is a safe
pre-installed system font (no substitute needed) or, if not, which
substitute font from the mapped table to use instead -- chosen by
geometric similarity (condensed-for-condensed, geometric-sans-for-
geometric-sans, serif-for-serif, etc.), not alphabetic proximity.

The system-font list and substitution table are ported verbatim (data,
not just the concept) from a real production presentation-rendering
pipeline's own font-fallback map (D:/elix/archive/platform_archive/
modules/presentation/pptx/font_fallback_map.py), which derived the
pairings empirically by geometric similarity.

Unlike the source (which falls through to an unverified direct-download
attempt for unknown fonts, since it runs in an environment with network
access to Google Fonts), this skill is local-only and never guesses --
an unknown/unmapped font name is refused loudly rather than silently
assumed to be downloadable or visually similar to anything in the table.

Usage:
    python resolve_font_fallback.py <font_declaration.json>

Exit 0 = resolved (system font, or found a mapped substitute), 1 =
reserved (unused; no partial/geometrically-impossible state applies
here), 2 = malformed input, or the font name has no known mapping.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

FONT_MAP_PATH = Path(__file__).parent.parent / "assets" / "font_fallback_map.json"


def _load_font_map() -> tuple[set[str], dict[str, str]]:
    data = json.loads(FONT_MAP_PATH.read_text(encoding="utf-8"))
    system_fonts = set(data["system_fonts"])  # already lowercase
    fallback_map = data["fallback_map"]
    return system_fonts, fallback_map


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python resolve_font_fallback.py <font_declaration.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        return 2

    if not isinstance(data, dict) or "font" not in data:
        print("ERROR: input must be an object with key 'font' (a font name string)", file=sys.stderr)
        return 2

    font = data["font"]
    if not isinstance(font, str) or not font.strip():
        print("ERROR: 'font' must be a non-empty string", file=sys.stderr)
        return 2
    font = font.strip()

    system_fonts, fallback_map = _load_font_map()

    if font.lower() in system_fonts:
        print(f"SYSTEM_FONT: '{font}' is pre-installed -- no substitute needed.")
        return 0

    # Case-insensitive exact match against the substitution table.
    lower_lookup = {k.lower(): (k, v) for k, v in fallback_map.items()}
    match = lower_lookup.get(font.lower())
    if match is not None:
        canonical_name, substitute = match
        print(f"SUBSTITUTE: '{canonical_name}' -> '{substitute}'")
        return 0

    print(
        f"ERROR: no fallback mapping exists for '{font}'. It is neither a known system font "
        f"nor present in the {len(fallback_map)}-entry substitution table. Refusing to guess a "
        f"substitute -- declare a font from the mapped table, or a pre-installed system font.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
