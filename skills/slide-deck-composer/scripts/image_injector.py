"""
Real picture injection: replace a cloned slide's actual embedded
picture with a caller-supplied image file, or a deterministic
network-free Pillow placeholder when no real image is supplied.

Generalized from a working proof-of-concept prototype built earlier
this session (`tests (ignore)/slide-deck-composer/swap_images.py`) --
that prototype swapped every embedded image's raw bytes at the
zip/media level, which correctly avoided python-pptx's SVG/EMF-decode
limitation and needed no shape-tree walking. This module keeps that
"never decode/re-encode the target shape's XML, only its image bytes"
spirit but moves the swap to the python-pptx relationship-part level
(`SlidePart.get_or_add_image_part`) instead of raw zip surgery, for
one concrete reason the prototype could not handle: `slide_duplicator
.duplicate_slide` re-relates each cloned slide's picture to the SAME
underlying image PART object (python-pptx does not duplicate media
bytes on `relate_to(rel.target_part, ...)`), so a raw zip-level byte
swap of `ppt/media/imageN.png` would silently overwrite that image
for EVERY slide sharing it, not just the one slide actually being
targeted. Adding/relating a fresh image part per replacement keeps
each slide's swap independent.

Granularity actually achieved (be honest, per SKILL.md discipline):
per-slide, single-picture -- `pick_best_picture` selects ONE top-level
(non-grouped, matching this skill's existing group-skip convention)
`Picture` shape per slide via `shape_roles.score_picture_shape`
(largest/most-centered wins). Multiple distinct pictures on the same
slide are not independently addressable in this round; only the
best-scoring one is replaced.

Aspect-ratio handling actually achieved: the replacement bitmap is
letterboxed (padded, not stretched) to match the TARGET SHAPE's own
declared frame aspect ratio (`shape.width/shape.height` in EMU) rather
than attempting full crop-aware resizing against the original photo's
`<a:srcRect>` -- and any existing `<a:srcRect>` crop on the shape is
explicitly removed, since a crop rectangle authored against the OLD
photo's pixels has no defined meaning against a brand-new image and
would otherwise silently produce a wrong, arbitrary crop of the
replacement. This is the "resize/letterbox to the frame's own aspect
ratio" tier described in this round's task brief, not full
photo-crop-aware resizing.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any

from PIL import Image
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

import placeholder_images
import shape_roles


class ImageInjectorError(Exception):
    """Raised for any refuse-loudly condition in this module."""


_LETTERBOX_PAD_RGB = (245, 245, 245)


def find_top_level_pictures(shapes) -> list[Any]:
    """Top-level Picture shapes only -- matches shape_roles.
    collect_text_shapes' deliberate decision to skip `<p:grpSp>` groups
    (see that module's docstring): a picture nested inside a decorative
    group is preserved untouched by the clone, never a valid injection
    target in this skill's v1/v2 scope."""
    out = []
    for shape in shapes:
        try:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                out.append(shape)
        except Exception:
            continue
    return out


def pick_best_picture(shapes, slide_width_emu: int, slide_height_emu: int):
    """Return the largest/most-centered top-level Picture shape on the
    slide, or None if the slide has no top-level picture at all."""
    candidates = find_top_level_pictures(shapes)
    if not candidates:
        return None
    scored = [
        (shape_roles.score_picture_shape(s, slide_width_emu, slide_height_emu), s)
        for s in candidates
    ]
    scored.sort(key=lambda t: -t[0])
    return scored[0][1]


def _letterbox_to_frame_aspect(image: Image.Image, frame_w_emu: int, frame_h_emu: int) -> Image.Image:
    """Pad (never stretch) `image` so its pixel aspect ratio matches the
    target shape frame's aspect ratio. Returns the image unchanged if
    the frame has no usable dimensions or already matches within
    tolerance."""
    if frame_w_emu <= 0 or frame_h_emu <= 0:
        return image.convert("RGB")
    target_ratio = frame_w_emu / frame_h_emu
    src_w, src_h = image.size
    if src_w <= 0 or src_h <= 0:
        return image.convert("RGB")
    src_ratio = src_w / src_h

    rgb = image.convert("RGB")
    if abs(src_ratio - target_ratio) < 0.01:
        return rgb

    if src_ratio > target_ratio:
        # Source is relatively wider than the frame -> pad top/bottom.
        new_h = max(src_h, round(src_w / target_ratio))
        canvas = Image.new("RGB", (src_w, new_h), _LETTERBOX_PAD_RGB)
        canvas.paste(rgb, (0, (new_h - src_h) // 2))
    else:
        # Source is relatively taller than the frame -> pad left/right.
        new_w = max(src_w, round(src_h * target_ratio))
        canvas = Image.new("RGB", (new_w, src_h), _LETTERBOX_PAD_RGB)
        canvas.paste(rgb, ((new_w - src_w) // 2, 0))
    return canvas


def replace_picture_image(picture_shape, slide_part, image_bytes: bytes) -> dict:
    """Replace `picture_shape`'s underlying image with `image_bytes`,
    letterboxed to the shape's own frame aspect ratio, and clear any
    pre-existing `<a:srcRect>` crop (see module docstring for why).
    The shape's position/size/effects/rotation XML is otherwise
    untouched -- only the blip relationship target and (if present)
    the crop rectangle are modified.

    Raises ImageInjectorError if `image_bytes` isn't a decodable
    raster image, or the shape has no `<a:blip>` element (i.e. isn't a
    standard raster picture -- refuse rather than silently no-op).
    """
    try:
        source_img = Image.open(io.BytesIO(image_bytes))
        source_img.load()
    except Exception as e:
        raise ImageInjectorError(f"replacement image bytes are not a decodable raster image: {e}") from e

    frame_w = int(picture_shape.width or 0)
    frame_h = int(picture_shape.height or 0)
    letterboxed = _letterbox_to_frame_aspect(source_img, frame_w, frame_h)

    buf = io.BytesIO()
    letterboxed.save(buf, format="PNG", optimize=True)
    final_bytes = buf.getvalue()

    image_part, rid = slide_part.get_or_add_image_part(io.BytesIO(final_bytes))

    blip = picture_shape._element.find(f".//{qn('a:blip')}")
    if blip is None:
        raise ImageInjectorError(
            "picture shape has no <a:blip> element -- not a standard raster "
            "picture, refusing to guess at a different injection point"
        )
    blip.set(qn("r:embed"), rid)

    cropped = False
    blip_fill = picture_shape._element.find(qn("p:blipFill"))
    if blip_fill is not None:
        src_rect = blip_fill.find(qn("a:srcRect"))
        if src_rect is not None:
            blip_fill.remove(src_rect)
            cropped = True

    return {
        "frame_width_emu": frame_w,
        "frame_height_emu": frame_h,
        "original_image_px": list(source_img.size),
        "final_image_px": list(letterboxed.size),
        "letterboxed": letterboxed.size != source_img.convert("RGB").size,
        "src_rect_cleared": cropped,
        "image_part_partname": str(image_part.partname),
    }


def inject_slide_image(
    new_slide, slide_width_emu: int, slide_height_emu: int,
    image_path: Path | None, placeholder_seed: str,
) -> dict | None:
    """High-level entry point used by compile_deck.py's LAYOUT_IMG
    branch. Picks the slide's best top-level picture and replaces it
    with `image_path`'s real file bytes, or (when `image_path` is
    None) a deterministic Pillow-generated placeholder seeded from
    `placeholder_seed` -- matching this skill's existing
    `placeholder_images.generate_placeholder_png` no-network fallback.

    Returns None if the slide has no top-level picture shape to inject
    into (caller decides whether that's a hard refuse or a soft skip --
    see compile_deck.py's LAYOUT_IMG branch, which treats it as a hard
    refuse when the caller explicitly asked for an image swap).
    """
    picture = pick_best_picture(new_slide.shapes, slide_width_emu, slide_height_emu)
    if picture is None:
        return None

    if image_path is not None:
        if not image_path.is_file():
            raise ImageInjectorError(f"image file not found: {image_path}")
        data = image_path.read_bytes()
        source = f"caller_file:{image_path}"
    else:
        data = placeholder_images.generate_placeholder_png(placeholder_seed)
        source = f"generated_placeholder:{hashlib.md5(placeholder_seed.encode('utf-8')).hexdigest()[:8]}"

    report = replace_picture_image(picture, new_slide.part, data)
    report["source"] = source
    report["shape_id"] = getattr(picture, "shape_id", None)
    return report
