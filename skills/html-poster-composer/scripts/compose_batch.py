#!/usr/bin/env python3
"""Renders N pages that share ONE layout.json template + a consistent style
into numbered per-page images (PNG/JPG) and/or one combined multi-page PDF
-- e.g. turning a structured document (any long-form content with a
repeating unit -- article sections, catalog entries, a slide-style
explainer) into a visually-consistent set of information pages. General
media/design capability, not tied to any one content domain (owner
directive, 2026-08-07): the SAME layout.json a single poster/banner already
uses works here unchanged, just filled with different content per page.

Reuses layout_schema.py/validate_content.py/font_embed.py and compose.py's
own zone-building (_build_zone_html) + auto-fit (_autofit_elements) --
never a second, drifting implementation of the same zone contract. Fonts
are declared ONCE at the top level and embedded ONCE in the combined HTML
(not repeated per page), avoiding N copies of the same base64 font blob.

Usage:
    python compose_batch.py <layout.json> <pages.json> -o out_dir [--pdf combined.pdf] [--format png|jpg]

pages.json shape:
    {
      "fonts": {"FamilyName": "path/to/font.ttf"},   // optional, shared by every page
      "pages": [
        {"zones": {<same content.json 'zones' shape, one entry per layout zone id>}},
        {"zones": {...}},
        ...
      ]
    }

Exit 0 = rendered, 1 = layout/any page's content validation failed OR a
text zone on any page could not be made to fit (every failing page+zone
named, not just the first), 2 = malformed input/args.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout_schema import CANVAS_PRESETS_MM, validate_layout, resolve_zone_positions  # noqa: E402
from validate_content import validate_content  # noqa: E402
from font_embed import build_font_face_css  # noqa: E402
from compose import _build_zone_html, _autofit_elements, _mm_to_px, ZONE_BASE_CSS  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("compose_batch.py requires 'playwright' + a Chromium binary (see html-poster-composer/SKILL.md compatibility).")

VALID_FORMATS = {"png", "jpg"}


def validate_pages(pages_data: dict, layout: dict, base_dir: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(pages_data, dict):
        return ["pages.json must be a JSON object"]

    pages = pages_data.get("pages")
    if not isinstance(pages, list) or not pages:
        errors.append("'pages' must be a non-empty list")
        return errors

    shared_fonts = pages_data.get("fonts", {})
    for i, page_entry in enumerate(pages):
        if not isinstance(page_entry, dict) or "zones" not in page_entry:
            errors.append(f"pages[{i}]: must be an object with a 'zones' key")
            continue
        # Reuses validate_content() exactly -- a per-page synthetic content.json
        # sharing the top-level 'fonts' declaration, never a parallel check.
        synthetic_content = {"zones": page_entry["zones"], "fonts": shared_fonts}
        page_errors = validate_content(layout, synthetic_content, base_dir)
        errors.extend(f"pages[{i}]: {e}" for e in page_errors)

    return errors


def build_batch_html(layout: dict, pages_data: dict, w_mm: float, h_mm: float, base_dir: Path) -> str:
    fonts = pages_data.get("fonts", {})
    font_face_css = build_font_face_css(fonts, base_dir) if fonts else ""
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'><style>",
        font_face_css,
        ZONE_BASE_CSS,
        f"@page {{ size: {w_mm}mm {h_mm}mm; margin: 0; }}",
        f".page{{width:{w_mm}mm;height:{h_mm}mm;background:#fff;position:relative;overflow:hidden;break-after:page;}}",
        ".page:last-child{break-after:auto;}",
        "</style></head><body>",
    ]
    for i, page_entry in enumerate(pages_data["pages"]):
        parts.append(f"<div class='page' data-page-index='{i}'>")
        for zone in layout["zones"]:
            parts.append(_build_zone_html(zone, page_entry["zones"][zone["id"]]))
        parts.append("</div>")
    parts.append("</body></html>")
    return "".join(parts)


def render_batch(layout: dict, pages_data: dict, base_dir: Path, out_dir: Path, out_pdf: Path | None, fmt: str) -> list[str]:
    w_mm, h_mm = CANVAS_PRESETS_MM[layout["canvas"]["preset"]]
    n_pages = len(pages_data["pages"])
    html_str = build_batch_html(layout, pages_data, w_mm, h_mm, base_dir)
    tmp_html = out_dir / "_batch_render.html"
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_html.write_text(html_str, encoding="utf-8")

    unfit: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": _mm_to_px(w_mm), "height": _mm_to_px(h_mm) * n_pages})
        page.goto(tmp_html.resolve().as_uri())
        unfit = _autofit_elements(page)

        if not unfit:
            page_divs = page.query_selector_all(".page")
            for i, div in enumerate(page_divs):
                box = div.bounding_box()
                out_img = out_dir / f"page_{i + 1:02d}.{fmt}"
                page.screenshot(path=str(out_img), clip=box, type="jpeg" if fmt == "jpg" else "png")

            if out_pdf is not None:
                page.emulate_media(media="print")
                page.pdf(path=str(out_pdf), print_background=True, prefer_css_page_size=True)

        browser.close()
    tmp_html.unlink()
    return unfit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layout_path")
    parser.add_argument("pages_path")
    parser.add_argument("-o", "--output", required=True, help="Output directory for numbered per-page images.")
    parser.add_argument("--pdf", help="Also export one combined multi-page vector PDF at this path.")
    parser.add_argument("--format", choices=sorted(VALID_FORMATS), default="png")
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

    layout_errors = validate_layout(layout)
    if layout_errors:
        print(f"INVALID layout ({len(layout_errors)} issue(s)):", file=sys.stderr)
        for e in layout_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    pages_path = Path(args.pages_path)
    if not pages_path.exists():
        print(f"ERROR: pages file not found: {pages_path}", file=sys.stderr)
        return 2
    try:
        pages_data = json.loads(pages_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {pages_path}: {e}", file=sys.stderr)
        return 2

    pages_errors = validate_pages(pages_data, layout, pages_path.parent)
    if pages_errors:
        print(f"INVALID pages.json ({len(pages_errors)} issue(s)):", file=sys.stderr)
        for e in pages_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    out_dir = Path(args.output)
    out_pdf = Path(args.pdf) if args.pdf else None
    unfit = render_batch(layout, pages_data, pages_path.parent, out_dir, out_pdf, args.format)
    if unfit:
        print(f"REFUSED: {len(unfit)} text zone(s) across all pages could not fit even at the minimum font size -- no file written:", file=sys.stderr)
        for u in unfit:
            print(f"  - {u}", file=sys.stderr)
        return 1

    n_pages = len(pages_data["pages"])
    print(f"OK: wrote {n_pages} page(s) to {out_dir} (page_01.{args.format} .. page_{n_pages:02d}.{args.format})" + (f" + {out_pdf}" if out_pdf else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
