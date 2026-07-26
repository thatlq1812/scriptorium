#!/usr/bin/env python3
"""Scaffold a minimal XeLaTeX book/report project with correct Vietnamese
setup (fontspec + polyglossia, not pdflatex + babel). Stdlib only.

Usage:
    python init_project.py <output_dir> [--title "Ten tai lieu"] [--font "Noto Serif"]
"""
from __future__ import annotations

import argparse
from pathlib import Path

MAIN_TEX = """\\documentclass[11pt]{{book}}
\\usepackage{{fontspec}}
\\usepackage{{polyglossia}}
\\setmainlanguage{{vietnamese}}
\\setmainfont{{{font}}}

\\usepackage[backend=biber,style=numeric]{{biblatex}}
\\addbibresource{{bibliography.bib}}

\\title{{{title}}}
\\author{{}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle
\\tableofcontents

\\input{{chapters/01_intro}}

\\printbibliography
\\end{{document}}
"""

CHAPTER_TEX = """\\chapter{{Giới thiệu}}

Nội dung chương đầu tiên. Trích dẫn ví dụ~\\cite{{example2026}}.
"""

BIBLIOGRAPHY_BIB = """@article{example2026,
  author  = {Nguyen, Van A},
  title   = {Vi du bibliography entry},
  journal = {Example Journal},
  year    = {2026},
}
"""

BUILD_SH = """#!/usr/bin/env bash
set -euo pipefail
xelatex main.tex
biber main
xelatex main.tex
xelatex main.tex
echo "OK: main.pdf"
"""

BUILD_PS1 = """$ErrorActionPreference = "Stop"
xelatex main.tex
biber main
xelatex main.tex
xelatex main.tex
Write-Host "OK: main.pdf"
"""


def scaffold(output_dir: Path, title: str, font: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "chapters").mkdir(exist_ok=True)

    (output_dir / "main.tex").write_text(MAIN_TEX.format(title=title, font=font), encoding="utf-8")
    (output_dir / "chapters" / "01_intro.tex").write_text(CHAPTER_TEX, encoding="utf-8")
    (output_dir / "bibliography.bib").write_text(BIBLIOGRAPHY_BIB, encoding="utf-8")
    (output_dir / "build.sh").write_text(BUILD_SH, encoding="utf-8")
    (output_dir / "build.ps1").write_text(BUILD_PS1, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--title", default="Tai lieu moi")
    parser.add_argument("--font", default="Noto Serif")
    args = parser.parse_args()

    scaffold(args.output_dir, args.title, args.font)
    print(f"OK: scaffold tại {args.output_dir} — build bằng build.sh/build.ps1 (cần xelatex + biber)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
