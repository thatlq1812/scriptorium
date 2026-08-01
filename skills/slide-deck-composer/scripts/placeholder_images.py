"""
Local, network-free placeholder-image generation (Pillow).

Standalone utility, NOT wired into compile_deck.py's v1 pipeline (v1
never replaces the template's own picture -- see SKILL.md "Known
limitations"). Provided so a future round (or a caller chaining this
skill with image-generator-gemini) has a deterministic, zero-network
fallback when no real image is available yet for an image-layout slide.

Re-implemented (not a verbatim line-for-line port -- the source
function pulls in a separately-licensed stock-photo inventory lookup
that this skill explicitly excludes per its brief) in the same spirit
as the "no network I/O, pure local generation via Pillow" path
documented in
D:/elix/archive/platform_archive/modules/presentation/pptx/placeholder_images.py's
``generate_placeholder_png`` docstring: an accent-banded rectangle with
a centered, word-wrapped caption and a small "illustration" tag so the
output is clearly flagged as a stand-in, never mistaken for a real
photo.
"""
from __future__ import annotations

import hashlib
import io

from PIL import Image, ImageDraw, ImageFont

_PALETTES: list[tuple[str, str]] = [
    ("#2B3A55", "#F2A65A"),
    ("#1B4332", "#95D5B2"),
    ("#3D348B", "#E6AF2E"),
    ("#7B2D26", "#F4E3B2"),
    ("#0B3954", "#BFD7EA"),
    ("#4A314D", "#E4C1F9"),
]


def _pick_palette(seed_text: str) -> tuple[str, str]:
    digest = hashlib.md5(seed_text.encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(_PALETTES)
    return _PALETTES[idx]


def _load_font(size: int) -> ImageFont.ImageFont:
    for candidate in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_caption(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def generate_placeholder_png(
    title: str, width_px: int = 1280, height_px: int = 720,
) -> bytes:
    """Render a deterministic, network-free placeholder PNG.

    Same title -> same palette + layout every time (hash-seeded), so
    repeated runs against the same content are reproducible.
    """
    base_hex, accent_hex = _pick_palette(title or "")
    img = Image.new("RGB", (width_px, height_px), base_hex)
    draw = ImageDraw.Draw(img)

    band_w = int(width_px * 0.08)
    draw.rectangle([0, 0, band_w, height_px], fill=accent_hex)

    caption = (title or "Illustration").strip() or "Illustration"
    font_size = max(28, int(height_px * 0.075))
    font = _load_font(font_size)

    text_left = band_w + int(width_px * 0.05)
    text_right = width_px - int(width_px * 0.05)
    text_width = text_right - text_left

    lines = _wrap_caption(draw, caption, font, text_width)
    if len(lines) > 3:
        lines = lines[:3]
        lines[-1] = lines[-1].rstrip(",.;:") + "..."

    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    total_h = sum(line_heights) + max(0, len(lines) - 1) * int(font_size * 0.3)

    y = int(height_px * 0.5 - total_h * 0.5)
    for line, lh in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = text_left + (text_width - line_w) // 2
        draw.text((x, y), line, fill=accent_hex, font=font)
        y += lh + int(font_size * 0.3)

    tag = "illustration"
    small_font = _load_font(max(14, int(height_px * 0.028)))
    tag_bbox = draw.textbbox((0, 0), tag, font=small_font)
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_h = tag_bbox[3] - tag_bbox[1]
    draw.text(
        (width_px - tag_w - int(width_px * 0.025), height_px - tag_h - int(height_px * 0.035)),
        tag, fill=accent_hex, font=small_font,
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer.getvalue()
