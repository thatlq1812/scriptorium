#!/usr/bin/env python3
"""Signboard/menu brand-identity structural + emphasis linter.

3 checks, each grounded in a real signboard/menu revision session this
project has direct access to (D:/elix/temp_project_20260728/brand-data.json
+ PROJECT.md's real client-feedback log, per UPGRADE_PLAN_20260729.md Item 4):

1. Color role completeness: primary/secondary/accent must each be declared
   with a valid hex color -- the real project's own color-priority system
   (primary = large blocks, secondary = accent/support, accent = CTA/price).
2. Emphasis (font-scaling) rule: any element flagged role "cta" or "contact"
   must have a font_size_pt >= the declared body_font_size_pt -- grounded in
   a real client note asking for exactly this ("ten mon...tang size",
   "chu dat hang/lien he co the to hon").
3. Icon-anchor / orphan-icon check: any icon element must reference a
   declared motif -- grounded in a real client complaint about "4 icon mo
   coi" (orphan icons with no thematic anchor) needing replacement with a
   themed motif instead.

Usage:
    python validate_brand.py <brand.json>

Exit 0 = valid, 1 = violations found (all printed), 2 = malformed input.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
REQUIRED_COLOR_ROLES = {"primary", "secondary", "accent"}
EMPHASIS_ROLES = {"cta", "contact"}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_brand.py <brand.json>", file=sys.stderr)
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

    if not isinstance(data, dict):
        print("ERROR: brand.json must be a JSON object.", file=sys.stderr)
        return 2

    errors: list[str] = []

    colors = data.get("colors")
    if not isinstance(colors, dict):
        errors.append("missing 'colors' object")
    else:
        for role in REQUIRED_COLOR_ROLES:
            if role not in colors:
                errors.append(f"colors: missing required role '{role}'")
                continue
            hex_val = colors[role].get("hex") if isinstance(colors[role], dict) else None
            if not hex_val or not HEX_RE.match(hex_val):
                errors.append(f"colors.{role}: 'hex' must be a valid #RRGGBB value, got {hex_val!r}")

    body_font_size = data.get("body_font_size_pt")
    if not isinstance(body_font_size, (int, float)) or body_font_size <= 0:
        errors.append("'body_font_size_pt' must be a positive number")

    motifs = data.get("motifs")
    if not isinstance(motifs, list):
        errors.append("'motifs' must be a list (may be empty if no icons declared)")
        motifs = []

    elements = data.get("elements")
    if not isinstance(elements, list) or not elements:
        errors.append("'elements' must be a non-empty list")
        elements = []

    for i, el in enumerate(elements):
        if not isinstance(el, dict) or "id" not in el or "type" not in el:
            errors.append(f"elements[{i}]: missing 'id' or 'type'")
            continue
        eid = el["id"]
        etype = el["type"]

        if etype in ("text",) and el.get("role") in EMPHASIS_ROLES and isinstance(body_font_size, (int, float)):
            font_size = el.get("font_size_pt")
            if not isinstance(font_size, (int, float)):
                errors.append(f"elements[{i}] ('{eid}'): role '{el.get('role')}' requires a numeric 'font_size_pt'")
            elif font_size < body_font_size:
                errors.append(
                    f"elements[{i}] ('{eid}'): role '{el.get('role')}' font_size_pt={font_size} "
                    f"is smaller than body_font_size_pt={body_font_size} -- emphasis elements must be >= body size"
                )

        if etype == "icon":
            motif_ref = el.get("motif_ref")
            if not motif_ref:
                errors.append(f"elements[{i}] ('{eid}'): icon has no 'motif_ref' -- orphan icon (no thematic anchor)")
            elif motif_ref not in motifs:
                errors.append(f"elements[{i}] ('{eid}'): motif_ref '{motif_ref}' not found in declared 'motifs' list")

    if errors:
        print(f"INVALID ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"VALID: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
