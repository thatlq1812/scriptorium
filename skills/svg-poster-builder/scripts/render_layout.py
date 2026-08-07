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

# v0.3.0 legibility fix: the old font_size = min(w, h) * 0.08 formula, with no
# floor, produced near-invisible labels on small zones (e.g. a 16.8x17.8mm
# decorative_element rendered at 1.3mm font-size). Clamped to a readable range.
MIN_LABEL_FONT_MM = 3.5
MAX_LABEL_FONT_MM = 11.0

# Legend band geometry (appended below the canvas, not part of the poster
# itself -- a preview aid so every zone is identifiable even when its own
# inline label is too small/cropped to read at a glance).
LEGEND_MARGIN_MM = 4.0
LEGEND_HEADER_HEIGHT_MM = 8.0
LEGEND_ROW_HEIGHT_MM = 6.5
LEGEND_SWATCH_SIZE_MM = 4.5


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


def _clamp_font_size(raw_mm: float) -> float:
    return max(MIN_LABEL_FONT_MM, min(MAX_LABEL_FONT_MM, raw_mm))


def _render_svg(layout: dict) -> str:
    w_mm, h_mm = CANVAS_PRESETS_MM[layout["canvas"]["preset"]]
    zones = layout["zones"]
    legend_height = LEGEND_HEADER_HEIGHT_MM + len(zones) * LEGEND_ROW_HEIGHT_MM + LEGEND_MARGIN_MM * 2
    total_h_mm = h_mm + legend_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_mm}mm" height="{total_h_mm:.1f}mm" '
        f'viewBox="0 0 {w_mm} {total_h_mm:.1f}">',
        f'  <rect x="0" y="0" width="{w_mm}" height="{total_h_mm:.1f}" fill="#FFFFFF"/>',
        f'  <rect x="0" y="0" width="{w_mm}" height="{h_mm}" fill="#FFFFFF" stroke="#000000" stroke-width="0.8"/>',
    ]
    for zone in zones:
        x = zone["x_pct"] / 100 * w_mm
        y = zone["y_pct"] / 100 * h_mm
        w = zone["w_pct"] / 100 * w_mm
        h = zone["h_pct"] / 100 * h_mm
        fill = zone.get("fill") or ZONE_DEFAULT_FILL.get(zone["type"], "#CCCCCC")
        # Real placeholder text (typography_frame) is shown inline since it's
        # the actual content preview; every other zone type shows only its
        # short id -- the full type name lives in the legend band below,
        # since cramming "id (type)" into a small icon/ornament-sized zone
        # is what made small zones unreadable before v0.3.0.
        if zone["type"] == "typography_frame":
            inline_label = zone.get("text_label", zone["id"])
        else:
            inline_label = zone["id"]
        font_size = _clamp_font_size(min(w, h) * 0.08 if min(w, h) > 0 else MIN_LABEL_FONT_MM)
        parts.append(f'  <g id="{zone["id"]}">')
        parts.append(f'    <rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="#333333" stroke-width="0.6"/>')
        parts.append(
            f'    <text x="{x + w / 2:.2f}" y="{y + h / 2:.2f}" font-size="{font_size:.1f}" '
            f'text-anchor="middle" dominant-baseline="middle" fill="#000000">{inline_label}</text>'
        )
        parts.append('  </g>')

    # Legend band: one row per zone (id, type, fill swatch, and text_label
    # when declared) so every zone is identifiable regardless of how small
    # or cluttered its own inline label is inside the canvas above.
    legend_y = h_mm + LEGEND_MARGIN_MM
    parts.append(f'  <line x1="0" y1="{h_mm}" x2="{w_mm}" y2="{h_mm}" stroke="#000000" stroke-width="0.8" stroke-dasharray="2,1.5"/>')
    parts.append(
        f'  <text x="{LEGEND_MARGIN_MM}" y="{legend_y + LEGEND_HEADER_HEIGHT_MM / 2:.1f}" '
        f'font-size="4.2" font-weight="bold" fill="#000000">Zone legend (preview aid -- not part of the printed poster)</text>'
    )
    row_y = legend_y + LEGEND_HEADER_HEIGHT_MM
    for zone in zones:
        fill = zone.get("fill") or ZONE_DEFAULT_FILL.get(zone["type"], "#CCCCCC")
        swatch_y = row_y + (LEGEND_ROW_HEIGHT_MM - LEGEND_SWATCH_SIZE_MM) / 2
        parts.append(
            f'  <rect x="{LEGEND_MARGIN_MM}" y="{swatch_y:.1f}" width="{LEGEND_SWATCH_SIZE_MM}" height="{LEGEND_SWATCH_SIZE_MM}" '
            f'fill="{fill}" stroke="#333333" stroke-width="0.4"/>'
        )
        text_label = zone.get("text_label")
        detail = f' -- "{text_label}"' if text_label else ""
        parts.append(
            f'  <text x="{LEGEND_MARGIN_MM + LEGEND_SWATCH_SIZE_MM + 2:.1f}" y="{swatch_y + LEGEND_SWATCH_SIZE_MM / 2 + 1.3:.1f}" '
            f'font-size="3.6" fill="#000000">{zone["id"]} ({zone["type"]}){detail}</text>'
        )
        row_y += LEGEND_ROW_HEIGHT_MM

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
