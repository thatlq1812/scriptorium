#!/usr/bin/env python3
"""Renders a poster/banner/flyer from a layout.json (+ optional content.json)
via real HTML/CSS through a headless Chromium browser (Playwright) --
replaces svg-poster-builder's SVG-string preview and poster-generator's
Pillow-based final render with ONE engine, since HTML/CSS can do both a
fast preview and a print-quality vector-preserving final export.

Same layout.json/content.json contract those 2 superseded skills used --
zone taxonomy, canvas presets, 40%-text-coverage rule (layout_schema.py),
content.json's image/text/fill-per-zone shape (validate_content.py). This
skill only changed HOW the JSON becomes pixels/vectors, not what the JSON
means.

Real fix for the exact bug class that motivated this migration (see
docs/ROADMAP.md's 2026-08-07 entry): the OLD Pillow renderer computed a
font size from a fixed formula (font_size_pct of the zone's declared
height) and just drew it -- if the actual wrapped text was taller than the
zone, it silently overflowed into whatever was below, no warning. This
renderer instead RENDERS FOR REAL, measures the actual rendered text-block
height via the browser's own layout engine (Playwright's bounding_box(),
not an approximation), and shrinks the font size and re-measures in a real
loop until it fits -- refusing loudly (exit 1) rather than silently
overflowing if no font size in the allowed range fits.

Usage:
    python compose.py <layout.json> -o preview.png --preview
    python compose.py <layout.json> <content.json> -o poster.png [--pdf poster.pdf] [--dpi 150]

Exit 0 = rendered, 1 = layout/content validation failed OR a text zone
could not be made to fit even at the minimum font size (all such zones
named, not just the first), 2 = malformed input/args.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout_schema import CANVAS_PRESETS_MM, ZONE_DEFAULT_FILL, validate_layout, resolve_zone_positions  # noqa: E402
from validate_content import validate_content  # noqa: E402
from font_embed import build_font_face_css  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit(
        "compose.py requires the 'playwright' package + a Chromium binary. "
        "Bootstrap via the 'browser-web-renderer' skill's check_browser.py/install_browser.ps1|sh "
        "(shared venv, same dependency this project already installs and audits)."
    )

CSS_PX_PER_INCH = 96.0  # CSS "mm"/"in" units are always defined relative to this, per the CSS spec -- fixed, not a DPI knob.
MM_PER_INCH = 25.4

DEFAULT_FONT_SIZE_PCT = 20.0
MIN_FONT_SIZE_PX = 8.0
FONT_SHRINK_FACTOR = 0.92
MAX_FIT_ATTEMPTS = 14
FIT_SAFETY_MARGIN = 0.98  # measured height must be <= this fraction of the zone's real height

LEGEND_ROW_HEIGHT_MM = 6.5
LEGEND_HEADER_HEIGHT_MM = 8.0
LEGEND_MARGIN_MM = 4.0
LEGEND_SWATCH_MM = 4.5

# Shared by compose_batch.py too -- never duplicate this string, a real bug
# was found from exactly that duplication drifting (see CSS comment below).
ZONE_BASE_CSS = (
    "*{box-sizing:border-box;font-family:Arial,sans-serif;margin:0;padding:0;}"
    ".text-wrap{width:100%;height:100%;display:flex;align-items:center;overflow:visible;}"
    # overflow-wrap is load-bearing, not cosmetic: .text-content is width:100% of its
    # zone, and the auto-fit loop below only ever measures/reacts to HEIGHT overflow,
    # trusting that word-wrap already keeps every line within the zone's width. A
    # single unbroken long token (no whitespace to wrap at, e.g. an 800-char string
    # with no spaces) breaks that trust without this rule -- found for real via
    # adversarial testing: it silently overflowed the canvas edge (clipped, content
    # lost, zero warning) while still measuring as a short SINGLE line, so the
    # height-only fit check saw nothing wrong and let it through.
    ".text-content{width:100%;line-height:1.25;overflow-wrap:break-word;word-break:break-word;}"
)


def _esc(s: str) -> str:
    return html_lib.escape(s, quote=True)


def _zone_style(zone: dict) -> str:
    return (
        f"position:absolute; left:{zone['x_pct']}%; top:{zone['y_pct']}%; "
        f"width:{zone['w_pct']}%; height:{zone['h_pct']}%; box-sizing:border-box; overflow:visible;"
    )


def _build_preview_html(layout: dict, w_mm: float, h_mm: float) -> str:
    zones = layout["zones"]
    legend_h_mm = LEGEND_HEADER_HEIGHT_MM + len(zones) * LEGEND_ROW_HEIGHT_MM + LEGEND_MARGIN_MM * 2
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'><style>",
        "*{box-sizing:border-box;font-family:Arial,sans-serif;margin:0;padding:0;}",
        f".page{{width:{w_mm}mm;height:{h_mm + legend_h_mm}mm;background:#fff;position:relative;}}",
        f".canvas{{width:{w_mm}mm;height:{h_mm}mm;position:relative;border:0.8mm solid #000;overflow:hidden;}}",
        ".zone-label{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;",
        "text-align:center;font-size:3.2mm;color:#000;padding:2mm;overflow:hidden;}",
        f".legend{{position:absolute;left:0;top:{h_mm}mm;width:{w_mm}mm;padding:{LEGEND_MARGIN_MM}mm;",
        "border-top:0.8mm dashed #000;}",
        ".legend h1{font-size:4.2mm;margin-bottom:2mm;}",
        ".legend .row{display:flex;align-items:center;gap:2mm;font-size:3.6mm;margin-bottom:1.5mm;}",
        f".legend .swatch{{width:{LEGEND_SWATCH_MM}mm;height:{LEGEND_SWATCH_MM}mm;border:0.4mm solid #333;flex:none;}}",
        "</style></head><body><div class='page'><div class='canvas'>",
    ]
    for zone in zones:
        fill = zone.get("fill") or ZONE_DEFAULT_FILL.get(zone["type"], "#CCCCCC")
        parts.append(f"<div style=\"{_zone_style(zone)}background:{fill};border:0.6mm solid #333;\">")
        parts.append(f"<div class='zone-label'>{_esc(zone['id'])}</div></div>")
    parts.append("</div><div class='legend'><h1>Zone legend (preview aid -- not part of the printed poster)</h1>")
    for zone in zones:
        fill = zone.get("fill") or ZONE_DEFAULT_FILL.get(zone["type"], "#CCCCCC")
        label = zone.get("text_label")
        detail = f" -- &quot;{_esc(label)}&quot;" if label else ""
        parts.append(
            f"<div class='row'><div class='swatch' style='background:{fill};'></div>"
            f"<div>{_esc(zone['id'])} ({zone['type']}){detail}</div></div>"
        )
    parts.append("</div></div></body></html>")
    return "".join(parts), h_mm + legend_h_mm


def _build_zone_html(zone: dict, entry: dict) -> str:
    """Builds one zone's HTML fragment (fill/image/text) -- shared by the
    single-page renderer and compose_batch.py's multi-page renderer, so the
    two never drift into two different implementations of the same zone
    contract."""
    etype = entry["type"]
    if etype == "fill":
        return f"<div data-zone='{_esc(zone['id'])}' style=\"{_zone_style(zone)}background:{entry['color']};\"></div>"
    if etype == "image":
        fit = "cover" if entry.get("fit", "cover") == "cover" else "contain"
        return (
            f"<div data-zone='{_esc(zone['id'])}' style=\"{_zone_style(zone)}\">"
            f"<img src='{_esc(Path(entry['path']).resolve().as_uri())}' style='width:100%;height:100%;object-fit:{fit};display:block;'></div>"
        )
    # text
    align = entry.get("align", "left")
    color = entry.get("color", "#000000")
    font_pct = entry.get("font_size_pct", DEFAULT_FONT_SIZE_PCT)
    font_family = entry.get("font_family")
    font_family_css = f"font-family:'{_esc(font_family)}';" if font_family else ""
    justify = {"left": "flex-start", "center": "center", "right": "flex-end"}.get(align, "flex-start")
    return (
        f"<div data-zone='{_esc(zone['id'])}' style=\"{_zone_style(zone)}\">"
        f"<div class='text-wrap' style='justify-content:{justify};'>"
        f"<div class='text-content' data-fit-target style=\"font-size:{font_pct}%;color:{color};text-align:{align};{font_family_css}\">"
        f"{_esc(entry['text'])}</div></div></div>"
    )


def _build_render_html(layout: dict, content: dict, w_mm: float, h_mm: float, base_dir: Path, transparent: bool = False) -> str:
    content_zones = content["zones"]
    font_face_css = build_font_face_css(content["fonts"], base_dir) if content.get("fonts") else ""
    canvas_bg = "transparent" if transparent else "#fff"
    # html/body default to a browser-painted white page background regardless
    # of .canvas's own background -- Playwright's omit_background screenshot
    # flag only drops THAT default page paint, so it must actually be
    # transparent (not just unset) for the flag to have anything to omit.
    page_bg_css = "html,body{background:transparent;}" if transparent else ""
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'><style>",
        font_face_css,
        ZONE_BASE_CSS,
        page_bg_css,
        f".canvas{{width:{w_mm}mm;height:{h_mm}mm;background:{canvas_bg};position:relative;overflow:hidden;}}",
        "</style></head><body><div class='canvas'>",
    ]
    for zone in layout["zones"]:
        parts.append(_build_zone_html(zone, content_zones[zone["id"]]))
    parts.append("</div></body></html>")
    return "".join(parts)


def _autofit_elements(page, selector: str = "[data-fit-target]") -> list[str]:
    """For every element matching selector, shrinks font-size until its real
    rendered bounding-box height fits inside its own zone's real bounding
    box (measured via the browser's own layout engine), or reports it as
    unfittable. Returns a list of zone ids that could not be made to fit.
    Pure fitting -- no screenshot/pdf side effects, so compose_batch.py can
    call this once per page (scoped selector) and do its own combined
    multi-page export afterward."""
    unfit: list[str] = []
    targets = page.query_selector_all(selector)
    for el in targets:
        zone_div = el.evaluate_handle("el => el.closest('[data-zone]')")
        zone_id = zone_div.evaluate("el => el.getAttribute('data-zone')")
        zone_box = zone_div.evaluate("el => { const r = el.getBoundingClientRect(); return {w: r.width, h: r.height}; }")

        # Start from the font-size % (of zone height) already set inline; convert to a real px value once.
        current_px = el.evaluate(
            "(el, zoneH) => { const cs = getComputedStyle(el); const pct = parseFloat(cs.fontSize); return Math.max(8, zoneH * (parseFloat(el.style.fontSize) / 100)); }",
            zone_box["h"],
        )
        el.evaluate("(el, px) => { el.style.fontSize = px + 'px'; }", current_px)

        fitted = False
        for _ in range(MAX_FIT_ATTEMPTS):
            box = el.bounding_box()
            if box is None:
                break
            # Width is never checked here: .text-content is CSS-declared width:100% of its
            # zone, so its own bounding box width always equals the zone's width regardless
            # of content -- word-wrap already guarantees no line exceeds that width. Height
            # is the only real unknown (depends on how many lines the text wraps to).
            if box["height"] <= zone_box["h"] * FIT_SAFETY_MARGIN:
                fitted = True
                break
            current_px *= FONT_SHRINK_FACTOR
            if current_px < MIN_FONT_SIZE_PX:
                break
            el.evaluate("(el, px) => { el.style.fontSize = px + 'px'; }", current_px)

        if not fitted:
            final_box = el.bounding_box()
            unfit.append(f"{zone_id} (needs ~{final_box['height']:.0f}px height, zone only has {zone_box['h']:.0f}px, even at {current_px:.1f}px font)")

    return unfit


def _mm_to_px(mm: float) -> int:
    return round(mm / MM_PER_INCH * CSS_PX_PER_INCH)


def render_preview(layout: dict, out_png: Path) -> None:
    w_mm, h_mm = CANVAS_PRESETS_MM[layout["canvas"]["preset"]]
    html_str, total_h_mm = _build_preview_html(layout, w_mm, h_mm)
    tmp_html = out_png.with_suffix(".preview.html")
    tmp_html.write_text(html_str, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": _mm_to_px(w_mm), "height": _mm_to_px(total_h_mm)})
        page.goto(tmp_html.resolve().as_uri())
        page.screenshot(path=str(out_png), full_page=True)
        browser.close()
    tmp_html.unlink()


def render_final(layout: dict, content: dict, out_png: Path, out_pdf: Path | None, base_dir: Path) -> list[str]:
    w_mm, h_mm = CANVAS_PRESETS_MM[layout["canvas"]["preset"]]
    transparent = bool(content.get("transparent_background"))
    html_str = _build_render_html(layout, content, w_mm, h_mm, base_dir, transparent=transparent)
    tmp_html = out_png.with_suffix(".render.html")
    tmp_html.write_text(html_str, encoding="utf-8")
    unfit: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": _mm_to_px(w_mm), "height": _mm_to_px(h_mm)})
        if out_pdf is not None:
            page.emulate_media(media="print")
        page.goto(tmp_html.resolve().as_uri())
        unfit = _autofit_elements(page)
        if not unfit:
            page.screenshot(path=str(out_png), full_page=False, omit_background=transparent)
            if out_pdf is not None:
                # Playwright's page.pdf() defaults to US Letter and drops CSS background colors
                # unless told otherwise -- both would silently produce a wrong-size, background-less
                # PDF for a real ISO 216 poster. width/height + print_background fix both.
                page.pdf(path=str(out_pdf), width=f"{w_mm}mm", height=f"{h_mm}mm", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()
    tmp_html.unlink()
    return unfit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layout_path")
    parser.add_argument("content_path", nargs="?")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--pdf", help="Also export a vector-preserving PDF at this path (final render mode only).")
    parser.add_argument("--preview", action="store_true", help="Layout-only preview -- no content.json needed.")
    args = parser.parse_args()

    layout_path = Path(args.layout_path)
    if not layout_path.exists():
        print(f"ERROR: layout file not found: {layout_path}", file=sys.stderr)
        return 2
    try:
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {layout_path}: {e}", file=sys.stderr)
        return 2

    resolved_zones, resolve_errors = resolve_zone_positions(layout)
    if resolve_errors:
        print(f"INVALID layout ({len(resolve_errors)} issue(s) resolving relative_to/anchor positions):", file=sys.stderr)
        for e in resolve_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    layout["zones"] = resolved_zones

    errors = validate_layout(layout)
    if errors:
        print(f"INVALID layout ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    out_png = Path(args.output)
    out_png.parent.mkdir(parents=True, exist_ok=True)

    if args.preview:
        render_preview(layout, out_png)
        print(f"Rendered preview ({len(layout['zones'])} zone(s)) -> {out_png}")
        return 0

    if not args.content_path:
        print("ERROR: content_path is required unless --preview is set.", file=sys.stderr)
        return 2
    content_path = Path(args.content_path)
    if not content_path.exists():
        print(f"ERROR: content file not found: {content_path}", file=sys.stderr)
        return 2
    try:
        content = json.loads(content_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {content_path}: {e}", file=sys.stderr)
        return 2

    content_errors = validate_content(layout, content, base_dir=content_path.parent)
    if content_errors:
        print(f"INVALID content ({len(content_errors)} issue(s)):", file=sys.stderr)
        for e in content_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    out_pdf = Path(args.pdf) if args.pdf else None
    unfit = render_final(layout, content, out_png, out_pdf, content_path.parent)
    if unfit:
        print(f"REFUSED: {len(unfit)} text zone(s) could not fit even at the minimum font size -- no file written:", file=sys.stderr)
        for u in unfit:
            print(f"  - {u}", file=sys.stderr)
        print("Fix: shorten the text, raise font_size_pct's ceiling isn't the issue here -- enlarge the zone, or shorten the content.", file=sys.stderr)
        return 1

    print(f"OK: wrote {out_png}" + (f" + {out_pdf}" if out_pdf else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
