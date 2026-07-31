#!/usr/bin/env python3
"""Deterministic SVG poster/banner/flyer layout renderer.

Zone taxonomy (hero_image, content_scene, vignette, decorative_element,
background_canvas, typography_frame) and their full-bleed/no-overflow
placement discipline are grounded in a real production layout system's
documented component-type schema (a real A1-poster rendering pipeline
this project has direct access to) -- not invented categories. This skill
renders LAYOUT ONLY (labeled placeholder rectangles at declared zones) --
it never generates the actual imagery/illustration content, which is
explicitly out of scope (no AI image generation inside Scriptorium, per
CLAUDE.md principle 8).

Canvas presets are real ISO 216 paper sizes in mm (A1 594x841, A4 210x297),
used directly as the SVG viewBox/width/height units.

Max text-coverage check: the total area of all `typography_frame` zones
must not exceed 40% of the canvas area -- ported from a real statistical
rules corpus (D:/elix/archive/platform_archive/modules/presentation/scoring/design_rules.py,
CONTENT_DENSITY["max_text_coverage_pct"], derived from 10 Canva + 149
Slidesgo templates / 7,854 slides). Zone area (`w_pct * h_pct`) is used as
the text-density proxy since that's the only content measure this zone
taxonomy actually carries -- `typography_frame` is the zone type whose sole
purpose is holding text. The source's companion rule,
CONTENT_DENSITY["min_whitespace_pct"] (>= 30% of the canvas must be empty),
is deliberately NOT ported: this taxonomy's own bundled fixture has a
`background_canvas` zone spanning the full 100% of the canvas by design
(see assets/layout_template.json's "master_anchor" zone), and zones are
documented as allowed to intentionally overlap (decorative elements over
content). A canvas-wide "sum of zone areas" whitespace measure would be
either meaningless (full-bleed background always "fills" 100%) or wrong
(overlap makes the sum overcount actual covered area) for this schema --
a forced fit, so it is skipped rather than contorting the skill.

Usage:
    python render_layout.py <layout.json> -o poster.svg

Exit 0 = rendered, 1 = layout violations found (all printed), 2 = malformed input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

CANVAS_PRESETS_MM = {
    "A1": (594, 841),
    "A4": (210, 297),
}

ZONE_TYPES = {
    "hero_image", "content_scene", "vignette", "decorative_element",
    "background_canvas", "typography_frame",
}

ZONE_DEFAULT_FILL = {
    "hero_image": "#E8C97A",
    "content_scene": "#B8D8BA",
    "vignette": "#F2B6A0",
    "decorative_element": "#D9C7F0",
    "background_canvas": "#F5E6C8",
    "typography_frame": "#FFFFFF",
}

REQUIRED_ZONE_KEYS = {"id", "type", "x_pct", "y_pct", "w_pct", "h_pct"}

# CONTENT_DENSITY["max_text_coverage_pct"] from design_rules.py (10 Canva +
# 149 Slidesgo templates / 7,854 slides).
MAX_TEXT_COVERAGE_PCT = 40.0


def _validate_layout(layout: dict) -> list[str]:
    errors: list[str] = []

    canvas = layout.get("canvas")
    if not isinstance(canvas, dict) or "preset" not in canvas:
        errors.append("missing 'canvas.preset'")
    elif canvas["preset"] not in CANVAS_PRESETS_MM:
        errors.append(f"unknown canvas.preset {canvas['preset']!r}, expected one of {sorted(CANVAS_PRESETS_MM)}")

    zones = layout.get("zones")
    if not isinstance(zones, list) or not zones:
        errors.append("'zones' must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    for i, zone in enumerate(zones):
        if not isinstance(zone, dict) or not REQUIRED_ZONE_KEYS.issubset(zone):
            errors.append(f"zones[{i}]: missing one of required keys {sorted(REQUIRED_ZONE_KEYS)}")
            continue
        zid = zone["id"]
        if zid in seen_ids:
            errors.append(f"zones[{i}]: duplicate zone id '{zid}'")
        seen_ids.add(zid)

        if zone["type"] not in ZONE_TYPES:
            errors.append(f"zones[{i}] ('{zid}'): unknown type {zone['type']!r}, expected one of {sorted(ZONE_TYPES)}")

        for key in ("x_pct", "y_pct", "w_pct", "h_pct"):
            val = zone[key]
            if not isinstance(val, (int, float)) or not (0 <= val <= 100):
                errors.append(f"zones[{i}] ('{zid}'): '{key}' must be a number in [0, 100], got {val!r}")

        if all(isinstance(zone[k], (int, float)) for k in ("x_pct", "w_pct")) and zone["x_pct"] + zone["w_pct"] > 100:
            errors.append(f"zones[{i}] ('{zid}'): x_pct + w_pct = {zone['x_pct'] + zone['w_pct']} exceeds canvas width (100)")
        if all(isinstance(zone[k], (int, float)) for k in ("y_pct", "h_pct")) and zone["y_pct"] + zone["h_pct"] > 100:
            errors.append(f"zones[{i}] ('{zid}'): y_pct + h_pct = {zone['y_pct'] + zone['h_pct']} exceeds canvas height (100)")

        if zone["type"] == "typography_frame" and not zone.get("text_label"):
            errors.append(f"zones[{i}] ('{zid}'): typography_frame zones must declare a non-empty 'text_label' (interior placeholder text)")

    total_text_coverage_pct = 0.0
    for zone in zones:
        if not isinstance(zone, dict) or zone.get("type") != "typography_frame":
            continue
        w_val, h_val = zone.get("w_pct"), zone.get("h_pct")
        if isinstance(w_val, (int, float)) and isinstance(h_val, (int, float)):
            total_text_coverage_pct += (w_val * h_val) / 100.0
    if total_text_coverage_pct > MAX_TEXT_COVERAGE_PCT:
        errors.append(
            f"zones: typography_frame zones cover {total_text_coverage_pct:.1f}% of the canvas, "
            f"exceeds max text coverage of {MAX_TEXT_COVERAGE_PCT}% (design_rules.py "
            "CONTENT_DENSITY['max_text_coverage_pct'], derived from 10 Canva + 149 Slidesgo "
            "templates / 7,854 slides)"
        )

    return errors


def _render_svg(layout: dict) -> str:
    w_mm, h_mm = CANVAS_PRESETS_MM[layout["canvas"]["preset"]]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_mm}mm" height="{h_mm}mm" '
        f'viewBox="0 0 {w_mm} {h_mm}">',
        f'  <rect x="0" y="0" width="{w_mm}" height="{h_mm}" fill="#FFFFFF"/>',
    ]
    for zone in layout["zones"]:
        x = zone["x_pct"] / 100 * w_mm
        y = zone["y_pct"] / 100 * h_mm
        w = zone["w_pct"] / 100 * w_mm
        h = zone["h_pct"] / 100 * h_mm
        fill = zone.get("fill") or ZONE_DEFAULT_FILL.get(zone["type"], "#CCCCCC")
        label = zone.get("text_label", zone["id"])
        parts.append(f'  <g id="{zone["id"]}">')
        parts.append(f'    <rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="#333333" stroke-width="0.5"/>')
        font_size = min(w, h) * 0.08 if min(w, h) > 0 else 4
        parts.append(
            f'    <text x="{x + w / 2:.2f}" y="{y + h / 2:.2f}" font-size="{font_size:.1f}" '
            f'text-anchor="middle" dominant-baseline="middle" fill="#000000">{label} ({zone["type"]})</text>'
        )
        parts.append('  </g>')
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout_path")
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    path = Path(args.layout_path)
    if not path.exists():
        print(f"ERROR: layout file not found: {path}", file=sys.stderr)
        return 2
    try:
        layout = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        return 2
    if not isinstance(layout, dict):
        print("ERROR: layout.json must be a JSON object.", file=sys.stderr)
        return 2

    errors = _validate_layout(layout)
    if errors:
        print(f"INVALID ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    svg = _render_svg(layout)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8", newline="\n")
    print(f"Rendered {len(layout['zones'])} zone(s) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
