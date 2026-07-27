#!/usr/bin/env python3
"""One-time build script for assets/reference-vn-nd30.docx -- the pandoc
`--reference-doc` template used by export_nd30_docx.py to export a vnnd30
document to DOCX without pandoc's default styling (Aptos font, blue/teal
heading colors) overriding NĐ 30/2020's real requirements (Times New Roman,
black text throughout).

Recipe adapted from D:/elix/praxis_csc/resources/templates/reference-vn.docx
(a real, working solution to this exact problem in a sibling project) --
schema/patch-points reused, no file/binary copied: take pandoc's own default
reference.docx (`pandoc --print-default-data-file reference.docx`) and patch:
  1. word/theme/theme1.xml -- majorFont/minorFont latin typeface -> "Times New Roman"
  2. word/styles.xml -- docDefaults rPr sz/szCs 24 (12pt) -> 26 (13pt, matching
     NĐ 30/2020's Phụ lục I nội dung văn bản cỡ 13-14)
  3. word/styles.xml -- every Heading1-9 (+ Char variant) w:color changed from
     pandoc's stock accent colors (0F4761/365F91/4F81BD/595959/272727) to
     000000 (black) -- this is the fix for the exact "blue/colored heading"
     bug that motivated building this file at all.

Requires `pandoc` on PATH (only at build time, not at export time -- the
patched .docx is committed to git like any other small template asset).
Run once; re-run only if the desired default font/size/heading-color changes.

Usage:
    python build_reference_docx.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

SKILL_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = SKILL_ROOT / "assets" / "reference-vn-nd30.docx"
STOCK_HEADING_COLORS = {"0F4761", "365F91", "4F81BD", "595959", "272727"}


def patch_theme1(xml: str) -> str:
    xml = re.sub(r'(<a:latin typeface=")Aptos Display(")', r"\1Times New Roman\2", xml)
    xml = re.sub(r'(<a:latin typeface=")Aptos(")', r"\1Times New Roman\2", xml)
    return xml


def patch_styles(xml: str) -> str:
    # docDefaults: 24 half-points (12pt) -> 26 half-points (13pt)
    xml = xml.replace('<w:sz w:val="24" />', '<w:sz w:val="26" />')
    xml = xml.replace('<w:szCs w:val="24" />', '<w:szCs w:val="26" />')
    for color in STOCK_HEADING_COLORS:
        xml = xml.replace(f'w:color w:val="{color}"', 'w:color w:val="000000"')
    return xml


def main() -> int:
    if shutil.which("pandoc") is None:
        print("BUILD FAILED: pandoc not found on PATH (only needed at build time).", file=sys.stderr)
        return 1

    result = subprocess.run(
        ["pandoc", "--print-default-data-file", "reference.docx"],
        capture_output=True, check=False,
    )
    if result.returncode != 0 or not result.stdout:
        print(f"BUILD FAILED: pandoc --print-default-data-file reference.docx: {result.stderr!r}", file=sys.stderr)
        return 1

    base_bytes = result.stdout
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    import io
    src = zipfile.ZipFile(io.BytesIO(base_bytes), "r")
    with zipfile.ZipFile(OUTPUT_PATH, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "word/theme/theme1.xml":
                data = patch_theme1(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/styles.xml":
                data = patch_styles(data.decode("utf-8")).encode("utf-8")
            dst.writestr(item, data)

    print(f"OK: wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
