#!/usr/bin/env python3
"""Mechanically split a full.md file into Dieu-level section files + a
nested index.json, driven by a structure.json the reviewing agent has
already verified against the source (see suggest_legal_boundaries.py for a
starting point -- this script trusts structure.json completely, it does no
semantic detection itself).

structure.json shape (1-indexed line numbers, matching how the Read tool
numbers lines):
{
  "sections": [
    {
      "heading": "Điều 1. Phạm vi điều chỉnh",
      "start_line": 5,
      "khoan": [
        {"heading": "1. ...", "start_line": 6,
         "diem": [{"heading": "a) ...", "start_line": 7}]}
      ]
    }
  ]
}

Each top-level entry becomes one section file (Dieu is the citable unit --
"Điều 5 Khoản 2" still needs Điều 5's full text for context, so khoan/diem
are recorded as line-anchored metadata inside the section, not split into
their own files).

Usage:
    python apply_legal_structure.py <full_md_file> <structure_json> <output_dir> [--overwrite]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

SLUG_RE = re.compile(r"[^a-z0-9]+")


def strip_diacritics(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))


def slugify(text: str, max_len: int = 60) -> str:
    slug = SLUG_RE.sub("-", strip_diacritics(text).lower()).strip("-")
    return (slug or "section")[:max_len]


def load_structure(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"structure.json is not valid JSON: {e}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict) or not isinstance(data.get("sections"), list):
        print("structure.json must be an object with a 'sections' array.", file=sys.stderr)
        raise SystemExit(2)
    if not data["sections"]:
        print("structure.json 'sections' is empty -- nothing to build.", file=sys.stderr)
        raise SystemExit(2)
    return data


def validate_sections(sections: list, total_lines: int) -> None:
    prev_start = 0
    for i, sec in enumerate(sections):
        for field in ("heading", "start_line"):
            if field not in sec:
                print(f"sections[{i}] missing required field '{field}'.", file=sys.stderr)
                raise SystemExit(2)
        start = sec["start_line"]
        if not isinstance(start, int) or start < 1 or start > total_lines:
            print(
                f"sections[{i}] start_line={start!r} out of bounds (file has {total_lines} lines).",
                file=sys.stderr,
            )
            raise SystemExit(2)
        if start <= prev_start:
            print(
                f"sections[{i}] start_line={start} is not strictly after the previous "
                f"section's start_line={prev_start} -- sections must be in ascending, "
                "non-overlapping order.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        prev_start = start


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("full_md_file", type=Path)
    parser.add_argument("structure_json", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--overwrite", action="store_true", help="allow writing into an existing output_dir")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    if not args.full_md_file.exists():
        print(f"Input not found: {args.full_md_file}", file=sys.stderr)
        return 1
    if not args.structure_json.exists():
        print(f"structure.json not found: {args.structure_json}", file=sys.stderr)
        return 1

    index_json_path = args.output_dir / "index.json"
    if index_json_path.exists() and not args.overwrite:
        print(
            f"{index_json_path} already exists. Pass --overwrite to replace it.",
            file=sys.stderr,
        )
        return 2

    structure = load_structure(args.structure_json)
    lines = args.full_md_file.read_text(encoding="utf-8").split("\n")
    validate_sections(structure["sections"], len(lines))

    sections_dir = args.output_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)

    manifest_sections = []
    raw_sections = structure["sections"]
    for i, sec in enumerate(raw_sections):
        start = sec["start_line"]
        end = raw_sections[i + 1]["start_line"] - 1 if i + 1 < len(raw_sections) else len(lines)
        body = "\n".join(lines[start - 1 : end]).strip()
        fname = f"{i:02d}-{slugify(sec['heading'])}.md"
        (sections_dir / fname).write_text(body, encoding="utf-8")
        manifest_sections.append(
            {
                "id": i,
                "heading": sec["heading"],
                "file": f"sections/{fname}",
                "start_line": start,
                "end_line": end,
                "char_count": len(body),
                "khoan": sec.get("khoan", []),
            }
        )

    manifest = {
        "source_file": str(args.full_md_file.name),
        "structure_mode": "legal",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "full_text_file": args.full_md_file.name,
        "sections": manifest_sections,
    }
    index_json_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"OK: {len(manifest_sections)} Điều sections -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
