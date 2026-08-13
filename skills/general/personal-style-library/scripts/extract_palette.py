#!/usr/bin/env python3
"""Extract the N most dominant colors from a real image via deterministic
pixel quantization (Pillow's adaptive palette quantization) -- real hex
values grounded in the image's actual pixel data, never guessed.

This is step 1 of a deliberate 2-step process (same "script proposes,
reviewing agent decides" discipline this project already applies elsewhere,
e.g. document-ai-structurer's catalog step): this script has no notion of
which extracted color should be "primary" vs "accent" -- that's a semantic
judgment only an agent that has actually looked at the image can make.
Output is ranked by pixel share only. To turn this into a real
palettes/<name>.json library entry, look at the source image, assign roles
to the swatches you judge fit (primary/secondary/accent/background), then
hand-write the entry and validate it with validate_library.py.

Usage:
    python extract_palette.py <image_path> -o swatches.json [--colors N]

N defaults to 6. Exit 0 = extracted, 2 = image not found/unreadable or
malformed args.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

try:
    from PIL import Image
except ImportError:
    sys.exit("extract_palette.py requires Pillow -- install via requirements.txt through the shared venv (see SKILL.md).")


def extract_dominant_colors(image_path: Path, num_colors: int) -> list[dict]:
    """Adaptive palette quantization (PIL's own MEDIANCUT-based ADAPTIVE
    method): reduces the image to num_colors representative colors, then
    counts how many pixels map to each -- a real, deterministic measure of
    dominance, not a guess. Returns swatches sorted by pixel_share_pct
    descending."""
    with Image.open(image_path) as im:
        im = im.convert("RGB")
        total_pixels = im.width * im.height
        quantized = im.quantize(colors=num_colors, method=Image.MEDIANCUT)
        palette = quantized.getpalette()[: num_colors * 3]
        get_flat = getattr(quantized, "get_flattened_data", quantized.getdata)
        index_counts = Counter(get_flat())

    swatches = []
    for index, count in index_counts.items():
        r, g, b = palette[index * 3 : index * 3 + 3]
        swatches.append(
            {
                "hex": f"#{r:02X}{g:02X}{b:02X}",
                "pixel_share_pct": round(count / total_pixels * 100, 2),
            }
        )
    swatches.sort(key=lambda s: s["pixel_share_pct"], reverse=True)
    return swatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image_path")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--colors", type=int, default=6, help="Number of dominant colors to extract (default 6).")
    args = parser.parse_args()

    if args.colors < 1 or args.colors > 32:
        print("ERROR: --colors must be between 1 and 32.", file=sys.stderr)
        return 2

    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"ERROR: image not found: {image_path}", file=sys.stderr)
        return 2

    try:
        swatches = extract_dominant_colors(image_path, args.colors)
    except Exception as e:  # Pillow raises varied exceptions for unreadable/corrupt images
        print(f"ERROR: could not read image {image_path}: {e}", file=sys.stderr)
        return 2

    result = {"source_image": str(image_path), "extracted_colors": swatches}
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8", newline="\n")

    print(f"Extracted {len(swatches)} dominant color(s) from {image_path} -> {out_path}")
    for s in swatches:
        print(f"  {s['hex']}  ({s['pixel_share_pct']}% of pixels)")
    print("These are UNASSIGNED swatches, ranked by pixel share only -- look at the image and assign roles (primary/secondary/accent/background) yourself when writing a palettes/<name>.json entry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
