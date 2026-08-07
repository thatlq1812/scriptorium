#!/usr/bin/env python3
"""Renders a circular seal/badge composition (ring border(s) + text curved
along an arc + an optional center image) -- a genuinely different shape
from the rectangular zone model the rest of this skill uses, elicited
directly from a real logo deliverable
(D:/elix/projects/temp_project_20260728/design/logo/logo-seal.svg, a real
25-<path> circular seal logo from a real client project) rather than
force-fit into the percentage-grid zone taxonomy.

Uses real SVG (not HTML/CSS) for the seal itself -- curved text needs
<textPath> along a real arc <path>, something CSS has no native equivalent
for, so this is exactly the case where SVG is still the right tool (see
docs/DECISIONS_PENDING.md-adjacent discussion: HTML replaced SVG for the
rectangular multi-zone poster problem specifically, not universally). The
generated SVG is then wrapped in HTML and rendered via the SAME
Playwright PNG/PDF export path the rest of this skill uses -- the exact
technique the real elicitation source's own export_pdf_logo_tem.py already
proved (SVG embedded in a sized HTML page, printed to PDF via Chromium).

Usage:
    python compose_seal.py <seal.json> -o seal.png [--pdf seal.pdf]

Exit 0 = rendered, 1 = spec validation failed, 2 = malformed input/args.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import math
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from font_embed import validate_fonts, build_font_face_css  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("compose_seal.py requires 'playwright' + a Chromium binary (see html-poster-composer/SKILL.md compatibility).")

CSS_PX_PER_INCH = 96.0
MM_PER_INCH = 25.4
HEX_RE_LEN = 7  # "#RRGGBB"


def _esc(s: str) -> str:
    return html_lib.escape(s, quote=True)


def _is_hex(v) -> bool:
    return isinstance(v, str) and v.startswith("#") and len(v) == HEX_RE_LEN


def validate_seal(spec: dict, base_dir: Path) -> list[str]:
    errors: list[str] = []

    diameter_mm = spec.get("diameter_mm")
    if not isinstance(diameter_mm, (int, float)) or diameter_mm <= 0:
        errors.append("'diameter_mm' must be a positive number")

    if "background_color" in spec and not _is_hex(spec["background_color"]):
        errors.append(f"'background_color' must be a hex string like '#RRGGBB', got {spec.get('background_color')!r}")

    rings = spec.get("rings", [])
    if not isinstance(rings, list):
        errors.append("'rings' must be a list (may be empty)")
        rings = []
    for i, ring in enumerate(rings):
        if not isinstance(ring, dict):
            errors.append(f"rings[{i}] must be an object")
            continue
        r = ring.get("radius_pct")
        if not isinstance(r, (int, float)) or not (0 < r <= 100):
            errors.append(f"rings[{i}].radius_pct must be a number in (0, 100], got {r!r}")
        if not _is_hex(ring.get("stroke_color")):
            errors.append(f"rings[{i}].stroke_color must be a hex string, got {ring.get('stroke_color')!r}")
        sw = ring.get("stroke_width_pct")
        if not isinstance(sw, (int, float)) or sw <= 0:
            errors.append(f"rings[{i}].stroke_width_pct must be a positive number, got {sw!r}")

    declared_families: set[str] = set()
    if "fonts" in spec:
        errors.extend(validate_fonts(spec["fonts"], base_dir))
        if isinstance(spec["fonts"], dict):
            declared_families = set(spec["fonts"])

    arc_text = spec.get("arc_text", [])
    if not isinstance(arc_text, list):
        errors.append("'arc_text' must be a list (may be empty)")
        arc_text = []
    for i, at in enumerate(arc_text):
        if not isinstance(at, dict):
            errors.append(f"arc_text[{i}] must be an object")
            continue
        if not isinstance(at.get("text"), str) or not at["text"].strip():
            errors.append(f"arc_text[{i}].text must be a non-empty string")
        r = at.get("radius_pct")
        if not isinstance(r, (int, float)) or not (0 < r <= 100):
            errors.append(f"arc_text[{i}].radius_pct must be a number in (0, 100], got {r!r}")
        for angle_key in ("start_deg", "end_deg"):
            v = at.get(angle_key)
            if not isinstance(v, (int, float)) or not (0 <= v < 360):
                errors.append(f"arc_text[{i}].{angle_key} must be a number in [0, 360), got {v!r}")
        if not _is_hex(at.get("color", "#000000")):
            errors.append(f"arc_text[{i}].color must be a hex string, got {at.get('color')!r}")
        if "letter_spacing_pct" in at and not isinstance(at["letter_spacing_pct"], (int, float)):
            errors.append(f"arc_text[{i}].letter_spacing_pct must be a number, got {at['letter_spacing_pct']!r}")
        font_family = at.get("font_family")
        if font_family is not None and font_family not in declared_families:
            errors.append(f"arc_text[{i}].font_family {font_family!r} is not declared in this seal's top-level 'fonts' object (declared: {sorted(declared_families)})")

    center_image = spec.get("center_image")
    if center_image is not None:
        if not isinstance(center_image, dict):
            errors.append("'center_image' must be an object if present")
        else:
            path = center_image.get("path")
            if not isinstance(path, str) or not path.strip():
                errors.append("center_image.path must be a non-empty string")
            else:
                resolved = Path(path) if Path(path).is_absolute() else base_dir / path
                if not resolved.is_file():
                    errors.append(f"center_image.path does not exist on disk: {resolved}")
            r = center_image.get("radius_pct")
            if not isinstance(r, (int, float)) or not (0 < r <= 100):
                errors.append(f"center_image.radius_pct must be a number in (0, 100], got {r!r}")

    return errors


def _arc_path_d(cx: float, cy: float, r: float, start_deg: float, end_deg: float) -> str:
    """SVG path 'd' tracing the arc segment from start_deg to end_deg going
    through increasing angle (standard math convention, 0=right/3-o'clock,
    90=down since SVG y is down) -- used as the invisible <path> a
    <textPath> rides along. Automatically reverses the path's OWN direction
    of travel (same visual arc, opposite endpoint order + opposite sweep
    flag) when the arc's midpoint sits in the bottom half of the circle --
    otherwise text placed along a bottom arc renders upside down (glyphs'
    'up' points toward the circle's center instead of away from it), a
    well-known SVG textPath quirk, found for real while building this
    (verified via a real 2-arc seal render: top text was correct on the
    first attempt, bottom text was mirrored/upside-down until this fix)."""
    sweep = (end_deg - start_deg) % 360
    large_arc = 1 if sweep > 180 else 0
    mid_deg = (start_deg + sweep / 2) % 360
    is_bottom_half = 0 < mid_deg < 180

    a_deg, b_deg = (end_deg, start_deg) if is_bottom_half else (start_deg, end_deg)
    sweep_flag = 0 if is_bottom_half else 1
    a_rad, b_rad = math.radians(a_deg), math.radians(b_deg)
    ax, ay = cx + r * math.cos(a_rad), cy + r * math.sin(a_rad)
    bx, by = cx + r * math.cos(b_rad), cy + r * math.sin(b_rad)
    return f"M {ax:.3f},{ay:.3f} A {r:.3f},{r:.3f} 0 {large_arc},{sweep_flag} {bx:.3f},{by:.3f}"


def build_svg(spec: dict, base_dir: Path) -> str:
    diameter_mm = spec["diameter_mm"]
    cx = cy = 500.0  # fixed internal coordinate space, scaled to diameter_mm by the outer <svg> viewBox
    outer_r = 480.0
    bg = spec.get("background_color", "#FFFFFF")

    defs, visible = [], []
    for i, at in enumerate(spec.get("arc_text", [])):
        r = at["radius_pct"] / 100 * outer_r
        path_id = f"arcpath{i}"
        defs.append(f'<path id="{path_id}" d="{_arc_path_d(cx, cy, r, at["start_deg"], at["end_deg"])}" fill="none"/>')
        font_family_attr = f' font-family="{_esc(at["font_family"])}"' if at.get("font_family") else ""
        font_size = at.get("font_size_pct", 8) / 100 * outer_r
        letter_spacing = at.get("letter_spacing_pct", 0) / 100 * outer_r
        visible.append(
            f'<text{font_family_attr} font-size="{font_size:.1f}" letter-spacing="{letter_spacing:.2f}" '
            f'fill="{at.get("color", "#000000")}" text-anchor="middle">'
            f'<textPath href="#{path_id}" startOffset="50%">{_esc(at["text"])}</textPath></text>'
        )

    rings_svg = []
    for ring in spec.get("rings", []):
        r = ring["radius_pct"] / 100 * outer_r
        sw = ring["stroke_width_pct"] / 100 * outer_r
        rings_svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.2f}" fill="none" stroke="{ring["stroke_color"]}" stroke-width="{sw:.2f}"/>')

    center_defs, center_body = "", ""
    center_image = spec.get("center_image")
    if center_image:
        r = center_image["radius_pct"] / 100 * outer_r
        img_path = Path(center_image["path"]) if Path(center_image["path"]).is_absolute() else base_dir / center_image["path"]
        center_defs = f'<clipPath id="centerclip"><circle cx="{cx}" cy="{cy}" r="{r:.2f}"/></clipPath>'
        center_body = (
            f'<image href="{_esc(img_path.resolve().as_uri())}" x="{cx - r:.2f}" y="{cy - r:.2f}" '
            f'width="{2 * r:.2f}" height="{2 * r:.2f}" preserveAspectRatio="xMidYMid slice" clip-path="url(#centerclip)"/>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 1000 1000" width="{diameter_mm}mm" height="{diameter_mm}mm">'
        f'<defs>{"".join(defs)}{center_defs}</defs>'
        f'<circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="{bg}"/>'
        f'{"".join(rings_svg)}'
        f'{center_body}'
        f'{"".join(visible)}'
        "</svg>"
    )


def render(spec: dict, base_dir: Path, out_png: Path, out_pdf: Path | None) -> None:
    diameter_mm = spec["diameter_mm"]
    font_face_css = build_font_face_css(spec["fonts"], base_dir) if spec.get("fonts") else ""
    svg_content = build_svg(spec, base_dir)
    html_content = (
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        f"{font_face_css}"
        f"@page {{ size: {diameter_mm}mm {diameter_mm}mm; margin: 0; }}"
        "html,body{margin:0;padding:0;}"
        f"svg{{display:block;width:{diameter_mm}mm;height:{diameter_mm}mm;}}"
        f"</style></head><body>{svg_content}</body></html>"
    )
    tmp_html = out_png.with_suffix(".seal.html")
    tmp_html.write_text(html_content, encoding="utf-8")

    w_px = round(diameter_mm / MM_PER_INCH * CSS_PX_PER_INCH)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w_px, "height": w_px}, device_scale_factor=2)
        page.goto(tmp_html.resolve().as_uri())
        page.wait_for_timeout(300)
        page.screenshot(path=str(out_png))
        if out_pdf is not None:
            page.pdf(path=str(out_pdf), width=f"{diameter_mm}mm", height=f"{diameter_mm}mm", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()
    tmp_html.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("seal_path")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--pdf")
    args = parser.parse_args()

    seal_path = Path(args.seal_path)
    if not seal_path.exists():
        print(f"ERROR: file not found: {seal_path}", file=sys.stderr)
        return 2
    try:
        spec = json.loads(seal_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {seal_path}: {e}", file=sys.stderr)
        return 2

    errors = validate_seal(spec, seal_path.parent)
    if errors:
        print(f"INVALID seal spec ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    out_png = Path(args.output)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_pdf = Path(args.pdf) if args.pdf else None
    render(spec, seal_path.parent, out_png, out_pdf)
    print(f"OK: wrote {out_png}" + (f" + {out_pdf}" if out_pdf else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
