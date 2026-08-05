#!/usr/bin/env python3
"""Renders a FINAL flattened poster PNG from a svg-poster-builder-compatible
layout.json (zone positions/sizes) + a content.json (what actually goes in
each zone -- an image path or text). Deterministic, PIL-based, no AI call --
the config-driven "template + fill zones with content" pattern from
auto-poster-generator (Apache-2.0), applied to svg-poster-builder's own zone
taxonomy instead of a fixed-coordinate template, so the same layout.json can
be BOTH previewed as placeholder SVG (svg-poster-builder) AND rendered as a
real poster (this skill) without maintaining two schemas.

Usage:
    python render_poster.py layout.json content.json poster.png --dpi 150
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_content import validate_content  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "svg-poster-builder" / "scripts"))
try:
    from render_layout import CANVAS_PRESETS_MM, _validate_layout  # noqa: E402
except ImportError:
    sys.exit(
        "render_poster.py requires the 'svg-poster-builder' skill installed as a "
        "sibling skill folder (.claude/skills/svg-poster-builder/) -- it reuses that "
        "skill's own layout schema and validator rather than duplicating them."
    )

MM_PER_INCH = 25.4

# Portable font fallback chain, tried in order when a content entry doesn't
# declare its own font_path -- PIL 12.x's ImageFont.load_default(size=...) is
# the guaranteed-always-available last resort (verified 2026-08-05: a real
# scalable default, not the old tiny bitmap font from older Pillow versions).
_SYSTEM_FONT_CANDIDATES = [
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _resolve_font(font_path: str | None, base_dir: Path, size: int) -> "ImageFont.FreeTypeFont":
    if font_path:
        resolved = Path(font_path) if Path(font_path).is_absolute() else base_dir / font_path
        return ImageFont.truetype(str(resolved), size)
    for candidate in _SYSTEM_FONT_CANDIDATES:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size=size)


def _mm_to_px(mm: float, dpi: int) -> int:
    return round(mm / MM_PER_INCH * dpi)


def _zone_box_px(zone: dict, canvas_w_px: int, canvas_h_px: int) -> tuple[int, int, int, int]:
    x = round(zone["x_pct"] / 100 * canvas_w_px)
    y = round(zone["y_pct"] / 100 * canvas_h_px)
    w = round(zone["w_pct"] / 100 * canvas_w_px)
    h = round(zone["h_pct"] / 100 * canvas_h_px)
    return x, y, w, h


def _paste_image_fit(canvas: Image.Image, image_path: Path, box: tuple[int, int, int, int], fit: str) -> None:
    x, y, w, h = box
    if w <= 0 or h <= 0:
        return
    img = Image.open(image_path).convert("RGBA")
    src_w, src_h = img.size
    src_ratio, box_ratio = src_w / src_h, w / h

    if fit == "cover":
        if src_ratio > box_ratio:
            new_h = h
            new_w = round(h * src_ratio)
        else:
            new_w = w
            new_h = round(w / src_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        crop_x = (new_w - w) // 2
        crop_y = (new_h - h) // 2
        img = img.crop((crop_x, crop_y, crop_x + w, crop_y + h))
        canvas.paste(img, (x, y))
    else:  # contain
        if src_ratio > box_ratio:
            new_w = w
            new_h = round(w / src_ratio)
        else:
            new_h = h
            new_w = round(h * src_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        offset_x = x + (w - new_w) // 2
        offset_y = y + (h - new_h) // 2
        canvas.paste(img, (offset_x, offset_y), img)


def _wrap_text(draw: "ImageDraw.ImageDraw", text: str, font: "ImageFont.FreeTypeFont", max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_text(canvas: Image.Image, entry: dict, box: tuple[int, int, int, int], base_dir: Path) -> None:
    x, y, w, h = box
    if w <= 0 or h <= 0:
        return
    draw = ImageDraw.Draw(canvas)
    text = entry["text"]
    color = entry.get("color", "#000000")
    align = entry.get("align", "center")

    font_size_pct = entry.get("font_size_pct", 20)
    font_size = max(8, round(h * font_size_pct / 100))
    font = _resolve_font(entry.get("font_path"), base_dir, font_size)

    lines = _wrap_text(draw, text, font, max_width=w)
    line_height = font.getbbox("Ag")[3] - font.getbbox("Ag")[1]
    total_text_h = line_height * len(lines)
    start_y = y + max(0, (h - total_text_h) // 2)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        if align == "center":
            line_x = x + (w - line_w) // 2
        elif align == "right":
            line_x = x + w - line_w
        else:
            line_x = x
        draw.text((line_x, start_y + i * line_height), line, font=font, fill=color)


def render(layout: dict, content: dict, base_dir: Path, dpi: int) -> Image.Image:
    w_mm, h_mm = CANVAS_PRESETS_MM[layout["canvas"]["preset"]]
    canvas_w_px, canvas_h_px = _mm_to_px(w_mm, dpi), _mm_to_px(h_mm, dpi)
    canvas = Image.new("RGBA", (canvas_w_px, canvas_h_px), "#FFFFFF")

    for zone in layout["zones"]:
        entry = content["zones"][zone["id"]]
        box = _zone_box_px(zone, canvas_w_px, canvas_h_px)
        if entry["type"] == "image":
            path = entry["path"]
            resolved = Path(path) if Path(path).is_absolute() else base_dir / path
            _paste_image_fit(canvas, resolved, box, entry.get("fit", "cover"))
        elif entry["type"] == "fill":
            x, y, w, h = box
            ImageDraw.Draw(canvas).rectangle([x, y, x + w, y + h], fill=entry["color"])
        else:
            _draw_text(canvas, entry, box, base_dir)

    return canvas.convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layout_path", type=Path)
    parser.add_argument("content_path", type=Path)
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--dpi", type=int, default=150, help="Pixels-per-inch for converting the layout's mm canvas to pixels (default 150)")
    args = parser.parse_args()

    for p in (args.layout_path, args.content_path):
        if not p.is_file():
            sys.exit(f"Not found: {p}")

    layout = json.loads(args.layout_path.read_text(encoding="utf-8"))
    content = json.loads(args.content_path.read_text(encoding="utf-8"))

    layout_errors = _validate_layout(layout)
    if layout_errors:
        print(f"INVALID layout.json, refusing to render ({len(layout_errors)} error(s)):")
        for err in layout_errors:
            print(f"  - {err}")
        return 1

    content_errors = validate_content(layout, content, base_dir=args.content_path.parent)
    if content_errors:
        print(f"INVALID content.json, refusing to render ({len(content_errors)} error(s)):")
        for err in content_errors:
            print(f"  - {err}")
        return 1

    image = render(layout, content, base_dir=args.content_path.parent, dpi=args.dpi)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output_path)
    print(f"OK: wrote {args.output_path} ({image.width}x{image.height}px @ {args.dpi}dpi)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
