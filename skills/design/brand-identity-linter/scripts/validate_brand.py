#!/usr/bin/env python3
"""Signboard/menu brand-identity structural + emphasis linter.

Checks, each grounded in real, statistically-backed sources this project
has direct access to:

1. Color-role RESOLUTION (not just presence): primary/secondary/accent
   are resolved via a deterministic fallback chain -- ported from a real
   production template-intelligence system's `PaletteBinding.role()`
   (D:/elix/archive/platform_archive/modules/presentation/template_intel/palette_binding.py):
     - primary: mandatory, no fallback (every other role roots here) --
       missing/invalid primary is an unrecoverable hard refusal.
     - secondary: declared, else falls back to the first declared accent
       color, else falls back to primary.
     - accent: declared (1-3 colors), else falls back to secondary, else
       falls back to primary.
   The report distinguishes "declared" from "resolved via fallback" for
   each role instead of a flat presence/absence pass-fail, per the real
   system's contract of "never returns nothing, always tells you what it
   resolved."
2. Max 3 accent colors -- ported from the real statistical rules corpus
   (D:/elix/archive/platform_archive/modules/presentation/scoring/design_rules.py,
   COLOR_RULES["max_accent_colors"], derived from 10 Canva + 149 Slidesgo
   templates / 7,854 slides).
3. Background is never pure white -- same source, COLOR_RULES's documented
   rule ("background is never pure white (#FFFFFF) in professional
   templates", backed by 8 catalogued real warm/cool off-white examples
   from the same template corpus). This skill enforces the hard boolean
   (reject literal #FFFFFF/#FFF) rather than restricting callers to the
   exact 8 catalogued hexes, since that catalogue is a sample of real
   values, not an exhaustive whitelist -- see SKILL.md for the full list
   kept as documented reference.
4. Emphasis (font-scaling) rule: any element flagged role "cta" or
   "contact" must have a font_size_pt >= the declared body_font_size_pt --
   grounded in a real client note asking for exactly this ("ten
   mon...tang size", "chu dat hang/lien he co the to hon").
5. Icon-anchor / orphan-icon check: any icon element must reference a
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
EMPHASIS_ROLES = {"cta", "contact"}

# COLOR_RULES["max_accent_colors"] from design_rules.py (10 Canva + 149
# Slidesgo templates / 7,854 slides).
MAX_ACCENT_COLORS = 3

# Pure-white forms rejected as background, per design_rules.py's
# "background is never pure white (#FFFFFF) in professional templates".
PURE_WHITE_HEXES = {"#FFFFFF", "#FFF"}

# Real catalogued off-white background examples from design_rules.py
# COLOR_RULES["warm_whites"] (8 templates from the 10-Canva/149-Slidesgo
# corpus). Kept here as documented reference for callers choosing a
# background color -- NOT enforced as an exhaustive whitelist, since it is
# a sample of real observed values, not the complete space of valid
# off-whites. The hard check below only rejects literal pure white.
CATALOGUED_OFF_WHITE_EXAMPLES = [
    "#F2EDE4",  # Minimalist Business
    "#FAF7F4",  # Pink Cream Scrapbook
    "#FBFFEA",  # Cookie template
    "#EFEBE2",  # Green Orange Playful
    "#FDF8F0",  # Warm preset
    "#F0F4F8",  # Professional Blue preset
    "#F5F7F5",  # Academic preset
    "#FAF5FF",  # Playful preset
]


def _entry_hex(entry) -> str | None:
    """Extract a 'hex' value from a {"hex": "#RRGGBB", ...} object, else None."""
    if isinstance(entry, dict):
        return entry.get("hex")
    return None


def _extract_accent_entries(raw) -> tuple[list[str], list[str]]:
    """Normalize colors.accent (single object OR list of objects) to a list
    of hex strings. Returns (hex_list, parse_errors). Does not validate hex
    format -- that's the caller's job, so format errors can be reported
    against the specific declared value.
    """
    if raw is None:
        return [], []
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return [], ["colors.accent: must be a hex-color object or a list of hex-color objects"]

    hexes: list[str] = []
    errors: list[str] = []
    for i, entry in enumerate(raw):
        hex_val = _entry_hex(entry)
        if not hex_val or not HEX_RE.match(hex_val):
            errors.append(f"colors.accent[{i}]: 'hex' must be a valid #RRGGBB value, got {hex_val!r}")
            continue
        hexes.append(hex_val)
    return hexes, errors


def resolve_colors(colors, errors: list[str]) -> dict | None:
    """Resolve primary/secondary/accent/background via the deterministic
    fallback chain ported from palette_binding.py's PaletteBinding.role().

    Returns a resolution dict on success:
        {
          "primary":    {"hex": "#...", "source": "declared"},
          "secondary":  {"hex": "#...", "source": "declared" | "fallback-to-accent" | "fallback-to-primary"},
          "accent":     {"hexes": ["#...", ...], "source": "declared" | "fallback-to-secondary" | "fallback-to-primary"},
          "background": {"hex": "#..." | None, "source": "declared" | "not-declared"},
        }
    Returns None if primary itself is missing/invalid -- unrecoverable,
    since every other role's fallback chain roots at primary (matches
    palette_binding.py's own root: everything ultimately falls back to
    primary, never returns nothing except when there is truly nothing to
    resolve from).
    """
    if not isinstance(colors, dict):
        errors.append("missing 'colors' object")
        return None

    # --- primary: mandatory, no fallback ---
    primary_hex = _entry_hex(colors.get("primary"))
    if not primary_hex or not HEX_RE.match(primary_hex):
        errors.append(
            f"colors.primary: 'hex' must be a valid #RRGGBB value, got {primary_hex!r} -- "
            "primary is required and has no fallback (every other color role's fallback "
            "chain resolves back to primary, so an invalid/missing primary is unrecoverable)"
        )
        return None

    resolution: dict = {"primary": {"hex": primary_hex, "source": "declared"}}

    # --- secondary: declared -> first accent -> primary ---
    secondary_raw = colors.get("secondary")
    secondary_declared_hex = _entry_hex(secondary_raw)
    if secondary_raw is not None and (not secondary_declared_hex or not HEX_RE.match(secondary_declared_hex)):
        errors.append(f"colors.secondary: declared but 'hex' is invalid, got {secondary_declared_hex!r}")

    # --- accent: declared (<=3) -> secondary -> primary ---
    accent_hexes, accent_parse_errors = _extract_accent_entries(colors.get("accent"))
    errors.extend(accent_parse_errors)
    if len(accent_hexes) > MAX_ACCENT_COLORS:
        errors.append(
            f"colors.accent: {len(accent_hexes)} accent color(s) declared, exceeds max of "
            f"{MAX_ACCENT_COLORS} (design_rules.py COLOR_RULES['max_accent_colors'], derived "
            "from 10 Canva + 149 Slidesgo templates / 7,854 slides)"
        )

    if secondary_declared_hex and HEX_RE.match(secondary_declared_hex):
        resolution["secondary"] = {"hex": secondary_declared_hex, "source": "declared"}
    elif accent_hexes:
        resolution["secondary"] = {"hex": accent_hexes[0], "source": "fallback-to-accent"}
    else:
        resolution["secondary"] = {"hex": primary_hex, "source": "fallback-to-primary"}

    if accent_hexes:
        resolution["accent"] = {"hexes": accent_hexes, "source": "declared"}
    elif secondary_declared_hex and HEX_RE.match(secondary_declared_hex):
        resolution["accent"] = {"hexes": [secondary_declared_hex], "source": "fallback-to-secondary"}
    else:
        resolution["accent"] = {"hexes": [primary_hex], "source": "fallback-to-primary"}

    # --- background: optional; if declared, must be valid hex and not pure white ---
    background_raw = colors.get("background")
    if background_raw is None:
        resolution["background"] = {"hex": None, "source": "not-declared"}
    else:
        background_hex = _entry_hex(background_raw)
        if not background_hex or not HEX_RE.match(background_hex):
            errors.append(f"colors.background: 'hex' must be a valid #RRGGBB value, got {background_hex!r}")
            resolution["background"] = {"hex": None, "source": "not-declared"}
        elif background_hex.upper() in PURE_WHITE_HEXES:
            errors.append(
                f"colors.background: '{background_hex}' is pure white -- backgrounds must not be pure "
                "white (design_rules.py COLOR_RULES, observed across the real template corpus). "
                f"Real catalogued off-white examples: {', '.join(CATALOGUED_OFF_WHITE_EXAMPLES)}"
            )
            resolution["background"] = {"hex": None, "source": "not-declared"}
        else:
            resolution["background"] = {"hex": background_hex, "source": "declared"}

    return resolution


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

    resolution = resolve_colors(data.get("colors"), errors)

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
    if resolution is not None:
        print("Color roles:")
        print(f"  - primary:    {resolution['primary']['hex']} ({resolution['primary']['source']})")
        print(f"  - secondary:  {resolution['secondary']['hex']} ({resolution['secondary']['source']})")
        print(f"  - accent:     {', '.join(resolution['accent']['hexes'])} ({resolution['accent']['source']})")
        bg = resolution["background"]
        bg_display = bg["hex"] if bg["hex"] else "(none declared)"
        print(f"  - background: {bg_display} ({bg['source']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
