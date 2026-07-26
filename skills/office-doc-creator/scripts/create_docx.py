#!/usr/bin/env python3
"""Create a .docx from a simple JSON content spec.

Usage:
    python create_docx.py <content.json> <output.docx>

content.json shape:
{
  "title": "Document Title",
  "blocks": [
    {"type": "heading", "level": 1, "text": "Section 1"},
    {"type": "paragraph", "text": "Some prose."},
    {"type": "table", "headers": ["A", "B"], "rows": [["1", "2"], ["3", "4"]]}
  ]
}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from docx import Document


def build(content: dict, output_path: Path) -> None:
    doc = Document()
    if content.get("title"):
        doc.add_heading(content["title"], level=0)

    for block in content.get("blocks", []):
        btype = block.get("type")
        if btype == "heading":
            doc.add_heading(block["text"], level=block.get("level", 1))
        elif btype == "paragraph":
            doc.add_paragraph(block["text"])
        elif btype == "table":
            headers = block.get("headers", [])
            rows = block.get("rows", [])
            table = doc.add_table(rows=1, cols=len(headers))
            table.style = "Light Grid Accent 1"
            for cell, header in zip(table.rows[0].cells, headers):
                cell.text = str(header)
            for row_data in rows:
                cells = table.add_row().cells
                for cell, value in zip(cells, row_data):
                    cell.text = str(value)
        else:
            raise ValueError(f"Unknown block type: {btype}")

    doc.save(str(output_path))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content_json", type=Path)
    parser.add_argument("output_docx", type=Path)
    args = parser.parse_args()

    content = json.loads(args.content_json.read_text(encoding="utf-8"))
    build(content, args.output_docx)
    print(f"OK: wrote {args.output_docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
