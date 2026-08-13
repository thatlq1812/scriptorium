#!/usr/bin/env python3
"""
Render every slide of a caller-supplied real .pptx template to a
labeled thumbnail grid image, so the CALLING AGENT can look at the
template's real slides and deliberately choose which one fits each
content block (via compile_deck.py's optional `source_slide_idx`
field) instead of the geometry-based heuristic in
`pick_source_slide_index` guessing blind.

This is the architectural fix for a real, repeatedly-hit problem
documented in SKILL.md's "Verified" bugs #6-10: automatic
slide-classification heuristics are an arms race against every new
template's idiosyncratic slide types (icon-grids, world-map
infographics, color-palette meta-slides). A human/agent looking at a
rendered thumbnail resolves the ambiguity instantly; a script guessing
from shape geometry alone cannot.

Pipeline: soffice --headless --convert-to pdf (real LibreOffice
subprocess, fixed argument list, no shell=True) -> pypdfium2 renders
each PDF page to a PNG -> Pillow composes a labeled grid JPG.

Label numbering is 0-based and lines up EXACTLY with the slide index
compile_deck.py expects in `source_slide_idx` (i.e. `prs.slides[i]`
for the same template file) -- this is the whole point of the tool,
so the numbering contract is load-bearing, not cosmetic.

Usage:
    python thumbnail_grid.py <template.pptx> <output_prefix> [--cols N] [--per-grid N]

Writes <output_prefix>_grid_1.jpg, _grid_2.jpg, ... (one grid image per
`--per-grid` slides, default 24, so a 149-slide template doesn't
produce one unreadably dense image) and prints a JSON manifest to
stdout: which slide indices landed in which grid file, image
dimensions, page count.

Exit codes: 0 = success, 2 = malformed/missing input, 3 = LibreOffice
conversion failed or produced no pages (refuse loudly, never guess).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

# Fixed path this project has already confirmed installed on this
# Windows box (see SKILL.md "Verified" -- used for the v0.1.1 visual
# review round's render-to-JPG loop). Overridable via --soffice for a
# different machine/OS, but the default matches this repo's confirmed
# environment.
_DEFAULT_SOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"

_THUMB_WIDTH_PX = 480
_LABEL_HEIGHT_PX = 32
_PADDING_PX = 8
_GRID_BG = (30, 30, 30)
_LABEL_BG = (0, 0, 0)
_LABEL_FG = (255, 220, 60)


class ThumbnailGridError(Exception):
    """Raised for any refuse-loudly condition in this tool."""


def _load_label_font(size: int) -> ImageFont.ImageFont:
    for candidate in ("arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_template_to_pdf(template_path: Path, workdir: Path, soffice: str) -> Path:
    """Convert the template .pptx to PDF via a real, fixed-argument-list
    LibreOffice subprocess call (no shell=True). This is the one
    legitimate new subprocess call this tool adds -- documented here
    explicitly per this project's security-check convention."""
    if not template_path.is_file():
        raise ThumbnailGridError(f"template file not found: {template_path}")
    if not Path(soffice).is_file():
        raise ThumbnailGridError(
            f"LibreOffice not found at {soffice!r} -- pass --soffice with the real path"
        )
    cmd = [
        soffice, "--headless", "--norestore", "--convert-to", "pdf",
        "--outdir", str(workdir), str(template_path),
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180, shell=False,
        )
    except subprocess.TimeoutExpired as e:
        raise ThumbnailGridError(f"LibreOffice conversion timed out: {e}") from e
    except OSError as e:
        raise ThumbnailGridError(f"failed to launch LibreOffice: {e}") from e
    expected_pdf = workdir / (template_path.stem + ".pdf")
    if proc.returncode != 0 or not expected_pdf.is_file():
        raise ThumbnailGridError(
            f"LibreOffice conversion failed (exit {proc.returncode}): "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    return expected_pdf


def pdf_to_thumbnails(pdf_path: Path, width_px: int = _THUMB_WIDTH_PX) -> list[Image.Image]:
    """Render every page of the PDF to a PIL Image at the given target
    width, preserving each page's real aspect ratio."""
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        images: list[Image.Image] = []
        for page_idx in range(len(pdf)):
            page = pdf[page_idx]
            page_w_pt, page_h_pt = page.get_size()
            scale = width_px / page_w_pt if page_w_pt else 1.0
            bitmap = page.render(scale=scale)
            pil_image = bitmap.to_pil().convert("RGB")
            images.append(pil_image)
        return images
    finally:
        pdf.close()


def _labeled_thumb(image: Image.Image, index: int, cell_w: int) -> Image.Image:
    """Return a thumbnail resized to fit cell_w, with a slide-index
    label bar composited above it. The label number is the 0-based
    slide index that MUST be passed as compile_deck.py's
    `source_slide_idx` to select this exact slide."""
    w, h = image.size
    scaled_h = max(1, int(h * (cell_w / w)))
    resized = image.resize((cell_w, scaled_h), Image.LANCZOS)

    cell = Image.new("RGB", (cell_w, scaled_h + _LABEL_HEIGHT_PX), _GRID_BG)
    draw = ImageDraw.Draw(cell)
    draw.rectangle([0, 0, cell_w, _LABEL_HEIGHT_PX], fill=_LABEL_BG)
    font = _load_label_font(int(_LABEL_HEIGHT_PX * 0.65))
    label = f"slide_idx={index}"
    draw.text((6, 5), label, fill=_LABEL_FG, font=font)
    cell.paste(resized, (0, _LABEL_HEIGHT_PX))
    return cell


def build_labeled_grids(
    thumbnails: list[Image.Image],
    output_prefix: Path,
    cols: int = 4,
    per_grid: int = 24,
) -> list[dict]:
    """Compose one or more labeled grid JPGs (chunked so a large
    template doesn't produce one unreadably dense image). Returns a
    manifest entry per grid file."""
    manifest: list[dict] = []
    total = len(thumbnails)
    cell_w = _THUMB_WIDTH_PX

    chunk_starts = list(range(0, total, per_grid))
    for grid_num, start in enumerate(chunk_starts, start=1):
        chunk_indices = list(range(start, min(start + per_grid, total)))
        cells = [_labeled_thumb(thumbnails[i], i, cell_w) for i in chunk_indices]
        rows = (len(cells) + cols - 1) // cols
        cell_h = max(c.size[1] for c in cells)
        grid_w = cols * (cell_w + _PADDING_PX) + _PADDING_PX
        grid_h = rows * (cell_h + _PADDING_PX) + _PADDING_PX
        grid_img = Image.new("RGB", (grid_w, grid_h), _GRID_BG)
        for pos, cell in enumerate(cells):
            r, c = divmod(pos, cols)
            x = _PADDING_PX + c * (cell_w + _PADDING_PX)
            y = _PADDING_PX + r * (cell_h + _PADDING_PX)
            grid_img.paste(cell, (x, y))

        out_path = output_prefix.parent / f"{output_prefix.name}_grid_{grid_num}.jpg"
        output_prefix.parent.mkdir(parents=True, exist_ok=True)
        grid_img.save(out_path, format="JPEG", quality=85)
        manifest.append({
            "file": str(out_path),
            "slide_indices": chunk_indices,
            "width_px": grid_w,
            "height_px": grid_h,
            "cols": cols,
        })
    return manifest


def generate_thumbnail_grid(
    template_path: Path,
    output_prefix: Path,
    cols: int = 4,
    per_grid: int = 24,
    soffice: str = _DEFAULT_SOFFICE,
) -> dict:
    with tempfile.TemporaryDirectory(prefix="slide-deck-composer-thumb-") as tmp:
        workdir = Path(tmp)
        pdf_path = render_template_to_pdf(template_path, workdir, soffice)
        thumbnails = pdf_to_thumbnails(pdf_path)
        if not thumbnails:
            raise ThumbnailGridError(
                f"LibreOffice produced a PDF with zero pages for {template_path}"
            )
        manifest = build_labeled_grids(thumbnails, output_prefix, cols=cols, per_grid=per_grid)

    return {
        "template": str(template_path),
        "slide_count": len(thumbnails),
        "grids": manifest,
        "note": (
            "Label numbers are 0-based and correspond exactly to prs.slides[i] "
            "for this template file -- pass the number shown as compile_deck.py's "
            "content.json slides[].source_slide_idx to clone that exact slide."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a labeled thumbnail grid of every slide in a real .pptx template."
    )
    parser.add_argument("template", type=Path, help="Caller-supplied .pptx template file")
    parser.add_argument("output_prefix", type=Path, help="Output path prefix for grid JPG(s)")
    parser.add_argument("--cols", type=int, default=4, help="Grid columns (default 4)")
    parser.add_argument(
        "--per-grid", type=int, default=24,
        help="Max slides per grid image before starting a new one (default 24)",
    )
    parser.add_argument(
        "--soffice", default=_DEFAULT_SOFFICE,
        help=f"Path to soffice executable (default: {_DEFAULT_SOFFICE})",
    )
    args = parser.parse_args()

    try:
        result = generate_thumbnail_grid(
            args.template, args.output_prefix, cols=args.cols,
            per_grid=args.per_grid, soffice=args.soffice,
        )
    except ThumbnailGridError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 - top-level CLI boundary
        print(f"ERROR: unexpected failure: {e}", file=sys.stderr)
        return 3

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
