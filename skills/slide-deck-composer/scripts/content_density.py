#!/usr/bin/env python3
"""
Content-density triage for a compiled or template .pptx: renders every
slide, grid-scans it for near-empty (low edge-density) regions, and
reports which slides are worth a closer look -- a fast, deterministic
PRE-FILTER, not a judge. A real deck's own review loop this session
(see slide-deck-composer's SKILL.md "Verified" bugs #6-10) required
rendering every slide to JPG and looking at it; for a 10-slide deck
that's cheap, for a 40+-slide deck it's a lot of image reads. This
script narrows that down to the slides actually worth spending an
image read on.

Deliberately NOT a decision-maker: a large empty region is not
automatically a defect (see slide-deck-composer's own "Zero-noise
delivery" example slide -- deliberately spacious, still good design).
This tool only flags CANDIDATES for review with a concrete empty-region
bounding box; whether to add content, leave it as intentional
whitespace, or place an image there is left entirely to the calling
agent's judgment.

Technique (grid_variance vs grid_edge_density -- see below): a naive
per-cell pixel-variance scan was tried first and rejected during this
tool's own design -- it false-flagged flat-color illustration blocks
(the dominant style in real Slidesgo templates) as "empty" purely
because each flat-color region is locally uniform. Edge density (PIL's
FIND_EDGES kernel, mean edge intensity per grid cell) correctly tells
"a flat-colored illustration" apart from "genuinely blank background",
since a color boundary still produces edge signal even inside a
uniformly-colored illustration block. This module implements the
edge-density approach only; the variance approach is documented here,
not shipped, because it was empirically wrong on a real test slide.

Usage:
    python content_density.py <deck.pptx> [--grid N] [--flag-threshold PCT]
        [--overlay-dir DIR] [--soffice PATH]

Prints a JSON report to stdout: per-slide empty_pct, the largest
contiguous empty rectangle (as a 0-1 fraction of slide width/height,
directly comparable to python-pptx EMU coordinates), and which slides
are flagged. Exit 0 always on a successful render+scan (this is a
report tool, not a refuse-loudly validator over content) -- exit 2/3
only for malformed input / render failure, matching this skill's other
scripts' exit-code convention.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from thumbnail_grid import (  # noqa: E402
    _DEFAULT_SOFFICE,
    ThumbnailGridError,
    pdf_to_thumbnails,
    render_template_to_pdf,
)

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

_RENDER_WIDTH_PX = 960  # higher than thumbnail_grid's 480 -- edge
                         # detection needs real detail, not a thumbnail
_DEFAULT_GRID = 16
_DEFAULT_FLAG_THRESHOLD_PCT = 55.0


class ContentDensityError(Exception):
    """Refuse-loudly condition (malformed input / render failure)."""


def _edge_density_grid(image: Image.Image, grid: int) -> np.ndarray:
    """Return a (grid, grid) array of normalized [0,1] edge-density
    scores, one per cell, 0 = flattest/emptiest cell in this slide,
    1 = busiest. Normalized PER-SLIDE (relative), not against a fixed
    absolute scale -- an intentionally minimal slide and a busy
    infographic slide have very different absolute edge levels, and
    what matters here is relative emptiness WITHIN one slide, not
    comparing raw edge magnitude across different slides."""
    gray = image.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    arr = np.array(edges, dtype=np.float32)
    h, w = arr.shape
    cell_h, cell_w = h // grid, w // grid
    if cell_h == 0 or cell_w == 0:
        raise ContentDensityError(
            f"rendered slide ({w}x{h}px) too small for a {grid}x{grid} grid"
        )
    density = np.zeros((grid, grid), dtype=np.float32)
    for r in range(grid):
        for c in range(grid):
            cell = arr[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w]
            density[r, c] = float(cell.mean())
    d_min, d_max = float(density.min()), float(density.max())
    if d_max - d_min < 1e-6:
        # Every cell equally flat (or equally busy) -- degenerate case,
        # not an error: report either all-empty or all-full explicitly
        # rather than dividing by ~0.
        return np.zeros((grid, grid), dtype=np.float32) if d_max < 1.0 else np.ones((grid, grid), dtype=np.float32)
    return (density - d_min) / (d_max - d_min)


def _largest_empty_rectangle(empty_mask: np.ndarray) -> tuple[int, int, int, int]:
    """Largest all-True axis-aligned rectangle in a boolean grid, via
    the standard per-row histogram + monotonic-stack method (O(rows*cols)).
    Returns (row0, col0, row_count, col_count) in GRID CELL units."""
    rows, cols = empty_mask.shape
    heights = np.zeros(cols, dtype=np.int32)
    best_area = 0
    best = (0, 0, 1, 1)
    for r in range(rows):
        heights = np.where(empty_mask[r], heights + 1, 0)
        stack: list[int] = []  # indices into heights, increasing height
        c = 0
        while c <= cols:
            h = heights[c] if c < cols else 0
            if not stack or h >= heights[stack[-1]]:
                stack.append(c)
                c += 1
            else:
                top = stack.pop()
                width = c if not stack else c - stack[-1] - 1
                area = int(heights[top]) * width
                if area > best_area:
                    best_area = area
                    row0 = r - int(heights[top]) + 1
                    col0 = (stack[-1] + 1) if stack else 0
                    best = (row0, col0, int(heights[top]), width)
    return best


def analyze_slide(image: Image.Image, grid: int, empty_cell_threshold: float) -> dict:
    density = _edge_density_grid(image, grid)
    empty_mask = density < empty_cell_threshold
    empty_pct = 100.0 * float(empty_mask.sum()) / empty_mask.size

    row0, col0, rh, rw = _largest_empty_rectangle(empty_mask)
    largest_rect = {
        "left_frac": round(col0 / grid, 3),
        "top_frac": round(row0 / grid, 3),
        "width_frac": round(rw / grid, 3),
        "height_frac": round(rh / grid, 3),
        "area_pct": round(100.0 * (rh * rw) / (grid * grid), 1),
    }
    return {
        "empty_pct": round(empty_pct, 1),
        "largest_empty_rect": largest_rect,
        "grid": grid,
        "empty_mask": empty_mask.astype(int).tolist(),
    }


def _overlay_image(image: Image.Image, analysis: dict) -> Image.Image:
    grid = analysis["grid"]
    mask = analysis["empty_mask"]
    w, h = image.size
    cell_w, cell_h = w / grid, h / grid
    vis = image.convert("RGB").copy()
    draw = ImageDraw.Draw(vis, "RGBA")
    for r in range(grid):
        for c in range(grid):
            if mask[r][c]:
                x0, y0 = c * cell_w, r * cell_h
                draw.rectangle([x0, y0, x0 + cell_w, y0 + cell_h], fill=(255, 0, 0, 70))
    rect = analysis["largest_empty_rect"]
    if rect["area_pct"] > 0:
        x0, y0 = rect["left_frac"] * w, rect["top_frac"] * h
        x1, y1 = x0 + rect["width_frac"] * w, y0 + rect["height_frac"] * h
        draw.rectangle([x0, y0, x1, y1], outline=(0, 200, 0, 255), width=4)
    return vis


def scan_deck(
    deck_path: Path, grid: int, flag_threshold_pct: float,
    empty_cell_threshold: float, overlay_dir: Path | None, soffice: str,
) -> dict:
    if not deck_path.is_file():
        raise ContentDensityError(f"deck file not found: {deck_path}")

    with tempfile.TemporaryDirectory(prefix="content_density_") as tmp:
        workdir = Path(tmp)
        try:
            pdf_path = render_template_to_pdf(deck_path, workdir, soffice)
            images = pdf_to_thumbnails(pdf_path, width_px=_RENDER_WIDTH_PX)
        except ThumbnailGridError as e:
            raise ContentDensityError(str(e)) from e

        if not images:
            raise ContentDensityError("render produced zero pages")

        if overlay_dir is not None:
            overlay_dir.mkdir(parents=True, exist_ok=True)

        slides: list[dict] = []
        for idx, image in enumerate(images):
            analysis = analyze_slide(image, grid, empty_cell_threshold)
            flagged = (
                analysis["empty_pct"] >= flag_threshold_pct
                or analysis["largest_empty_rect"]["area_pct"] >= flag_threshold_pct
            )
            record = {
                "slide_idx": idx,
                "empty_pct": analysis["empty_pct"],
                "largest_empty_rect": analysis["largest_empty_rect"],
                "flagged_for_review": flagged,
            }
            if overlay_dir is not None and flagged:
                overlay = _overlay_image(image, analysis)
                overlay_path = overlay_dir / f"slide_{idx:02d}_density.jpg"
                overlay.save(overlay_path, quality=70)
                record["overlay_image"] = str(overlay_path)
            slides.append(record)

    flagged_count = sum(1 for s in slides if s["flagged_for_review"])
    return {
        "deck": str(deck_path),
        "slide_count": len(slides),
        "flagged_count": flagged_count,
        "flag_threshold_pct": flag_threshold_pct,
        "note": (
            "flagged_for_review means 'worth a closer look', not 'defective' -- "
            "intentional whitespace is a valid design choice, this tool doesn't "
            "know the difference and doesn't try to."
        ),
        "slides": slides,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a deck and flag slides with a large empty/low-content region, for triage."
    )
    parser.add_argument("deck", type=Path, help="Compiled or template .pptx to scan")
    parser.add_argument("--grid", type=int, default=_DEFAULT_GRID, help=f"Grid resolution NxN (default {_DEFAULT_GRID})")
    parser.add_argument(
        "--flag-threshold", type=float, default=_DEFAULT_FLAG_THRESHOLD_PCT,
        help=f"Flag a slide when its empty_pct or largest empty rectangle exceeds this %% (default {_DEFAULT_FLAG_THRESHOLD_PCT})",
    )
    parser.add_argument(
        "--empty-cell-threshold", type=float, default=0.06,
        help="Normalized [0,1] per-cell edge-density below which a cell counts as empty (default 0.06, tuned against a real Slidesgo slide render)",
    )
    parser.add_argument("--overlay-dir", type=Path, default=None, help="If set, write a red-tinted overlay JPG per flagged slide here")
    parser.add_argument("--soffice", default=_DEFAULT_SOFFICE, help="Path to LibreOffice soffice executable")
    args = parser.parse_args()

    try:
        result = scan_deck(
            args.deck, args.grid, args.flag_threshold,
            args.empty_cell_threshold, args.overlay_dir, args.soffice,
        )
    except ContentDensityError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
