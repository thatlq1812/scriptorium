#!/usr/bin/env python3
"""Scan a markdown text file (typically full.md from structure_doc.py) for
CANDIDATE Vietnamese legal-document boundaries (Dieu / Khoan / Diem), using
regex heuristics only.

This is a suggestion tool, not an authority. It exists so the reviewing
agent does not have to scan a long document by hand for every "Dieu N."
line, but every candidate it emits MUST be checked by the agent against the
actual source before being used to build structure.json for
apply_legal_structure.py -- Docling's OCR/layout extraction on scanned
Vietnamese legal PDFs is not verified by this tool, and regex over markdown
text produces false positives (any numbered list looks like a Khoan/Diem).

Line numbers are 1-indexed, matching how the Read tool numbers lines --
review candidates by opening full.md with line numbers visible.

Usage:
    python suggest_legal_boundaries.py <full_md_file> [-o candidates.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DIEU_RE = re.compile(r"^\s{0,3}(?:#{1,6}\s*)?(?:\*\*)?Đi[eề]u\s+(\d+)\.?\s*(.*?)(?:\*\*)?\s*$")
KHOAN_RE = re.compile(r"^\s{0,3}(\d{1,3})\.\s+(.*)$")
DIEM_RE = re.compile(r"^\s{0,3}([a-zđ])\)\s+(.*)$")


def find_dieu_spans(lines: list[str]) -> list[tuple[int, int, str, str]]:
    """Return (line_no, next_dieu_line_no_or_len, number, heading_text)."""
    hits = []
    for i, line in enumerate(lines, start=1):
        m = DIEU_RE.match(line)
        if m:
            hits.append((i, m.group(1), m.group(2).strip()))
    spans = []
    for idx, (line_no, number, heading) in enumerate(hits):
        end = hits[idx + 1][0] - 1 if idx + 1 < len(hits) else len(lines)
        spans.append((line_no, end, number, heading))
    return spans


def find_khoan_in_span(lines: list[str], start: int, end: int) -> list[dict]:
    khoan = []
    for i in range(start, end + 1):
        if i - 1 >= len(lines):
            break
        m = KHOAN_RE.match(lines[i - 1])
        if m:
            khoan.append({"heading": lines[i - 1].strip(), "start_line": i})

    for k_idx, k in enumerate(khoan):
        k_end = khoan[k_idx + 1]["start_line"] - 1 if k_idx + 1 < len(khoan) else end
        diem = []
        for i in range(k["start_line"] + 1, k_end + 1):
            if i - 1 >= len(lines):
                break
            m = DIEM_RE.match(lines[i - 1])
            if m:
                diem.append({"heading": lines[i - 1].strip(), "start_line": i})
        k["diem"] = diem
    return khoan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("full_md_file", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None, help="write JSON here instead of stdout")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    if not args.full_md_file.exists():
        print(f"Input not found: {args.full_md_file}", file=sys.stderr)
        return 1

    text = args.full_md_file.read_text(encoding="utf-8")
    lines = text.split("\n")

    dieu_spans = find_dieu_spans(lines)
    if not dieu_spans:
        print(
            "No 'Dieu N.' pattern found -- either this isn't a Vietnamese "
            "legal-article document, or Docling's extraction mangled the "
            "heading text (check full.md by hand before assuming there's "
            "nothing to structure).",
            file=sys.stderr,
        )
        return 1

    sections = []
    for line_no, end_line, number, heading in dieu_spans:
        khoan = find_khoan_in_span(lines, line_no + 1, end_line)
        sections.append(
            {
                "heading": f"Điều {number}. {heading}".strip(),
                "start_line": line_no,
                "khoan": khoan,
            }
        )

    candidates = {
        "_warning": (
            "UNVERIFIED CANDIDATES -- regex heuristics only, false positives "
            "expected in 'khoan'/'diem' (any numbered/lettered list matches). "
            "Review every entry against the source before writing "
            "structure.json for apply_legal_structure.py. Do not trust "
            "Docling's OCR/layout extraction blindly either -- spot-check "
            "full.md against the original document first."
        ),
        "source_file": str(args.full_md_file.name),
        "sections": sections,
    }

    out = json.dumps(candidates, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"OK: {len(sections)} candidate Điều found -> {args.output}", file=sys.stderr)
    else:
        print(out)

    print(
        f"Reminder: {len(sections)} candidate Điều, review before use -- see _warning field.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
