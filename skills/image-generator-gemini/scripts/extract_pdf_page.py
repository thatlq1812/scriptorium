#!/usr/bin/env python3
"""Render a page of an existing PDF as a PNG — for pulling a cover thumbnail
out of a document rather than generating a new one. Uses pypdfium2 (already
a transitive dependency via docling in this repo's shared venv — no extra
network call, no AI API involved, purely local rendering).

Usage:
    python extract_pdf_page.py <input.pdf> <output.png> [--page 0] [--scale 2.0]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import pypdfium2 as pdfium
except ImportError:
    sys.exit("pypdfium2 not installed — should already be present via docling's transitive deps in the shared venv.")


def extract(pdf_path: Path, output_path: Path, page_index: int, scale: float) -> tuple[int, int]:
    pdf = pdfium.PdfDocument(str(pdf_path))
    if page_index >= len(pdf):
        raise ValueError(f"PDF chỉ có {len(pdf)} trang, không có trang index {page_index}")
    page = pdf[page_index]
    bitmap = page.render(scale=scale)
    pil_image = bitmap.to_pil()
    pil_image.save(output_path)
    return pil_image.size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("output_png", type=Path)
    parser.add_argument("--page", type=int, default=0, help="Index trang (0-based, mặc định trang đầu)")
    parser.add_argument("--scale", type=float, default=2.0, help="Hệ số render (2.0 ~ 144 DPI cho trang chuẩn)")
    args = parser.parse_args()

    if not args.input_pdf.exists():
        sys.exit(f"Không tìm thấy {args.input_pdf}")

    width, height = extract(args.input_pdf, args.output_png, args.page, args.scale)
    print(f"OK: wrote {args.output_png} ({width}x{height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
