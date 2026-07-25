#!/usr/bin/env python3
"""Convert a source document (PDF, DOCX, PPTX, XLSX, HTML, image...) into an
AI-optimized directory structure: full.md + sections/*.md (split on level-2
headings) + an index.json manifest. Images are extracted and referenced, not
embedded inline, to keep section files small.

Usage:
    python structure_doc.py <input_file> <output_dir>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc import ImageRefMode

DOCLING_VERSION = "2.115.0"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug or "section")[:max_len]


def split_sections(full_md: str) -> list[dict]:
    """Split markdown on level-2 (##) headings. Content before the first ##
    (title + any level-1 heading) becomes section 00-front-matter."""
    matches = list(HEADING_RE.finditer(full_md))
    level2 = [m for m in matches if len(m.group(1)) == 2]

    sections = []
    if not level2:
        sections.append({"heading": "Document", "level": 1, "body": full_md})
        return sections

    front = full_md[: level2[0].start()].strip()
    if front:
        sections.append({"heading": "Front matter", "level": 0, "body": front})

    for i, m in enumerate(level2):
        start = m.start()
        end = level2[i + 1].start() if i + 1 < len(level2) else len(full_md)
        sections.append(
            {"heading": m.group(2).strip(), "level": 2, "body": full_md[start:end].strip()}
        )
    return sections


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    input_path: Path = args.input_file
    output_dir: Path = args.output_dir
    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = output_dir / "sections"
    sections_dir.mkdir(exist_ok=True)

    converter = DocumentConverter()
    result = converter.convert(str(input_path))
    doc = result.document

    full_md_path = output_dir / "full.md"
    doc.save_as_markdown(full_md_path, image_mode=ImageRefMode.REFERENCED)
    full_md = full_md_path.read_text(encoding="utf-8")

    sections = split_sections(full_md)
    manifest_sections = []
    for i, sec in enumerate(sections):
        fname = f"{i:02d}-{slugify(sec['heading'])}.md"
        (sections_dir / fname).write_text(sec["body"], encoding="utf-8")
        manifest_sections.append(
            {
                "id": i,
                "heading": sec["heading"],
                "level": sec["level"],
                "file": f"sections/{fname}",
                "char_count": len(sec["body"]),
            }
        )

    images = [
        {"id": i, "ref": pic.self_ref}
        for i, pic in enumerate(getattr(doc, "pictures", []) or [])
    ]

    manifest = {
        "source_file": str(input_path.name),
        "title": doc.name or input_path.stem,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": f"docling {DOCLING_VERSION}",
        "full_text_file": "full.md",
        "sections": manifest_sections,
        "images": images,
    }
    (output_dir / "index.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"OK: {len(manifest_sections)} sections, {len(images)} images -> {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
