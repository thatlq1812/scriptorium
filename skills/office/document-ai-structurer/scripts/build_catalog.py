#!/usr/bin/env python3
"""Aggregate multiple document-ai-structurer legal-article-mode outputs
(each a folder with an index.json where structure_mode == "legal") into one
catalog.json an agent can query across documents, and legal-citation-checker
can use to verify a cited Điều number actually exists in the cited document
-- not just that the citation is well-formed.

Each source folder may optionally carry a doc_meta.json sibling (next to its
index.json) declaring van_ban_so_hieu/van_ban_ten -- the exact field names
legal-citation-checker already uses -- so a citation can be matched to a
document by số hiệu. This is caller-declared, never invented: a folder
without doc_meta.json is still included in the catalog (identified by its
folder name only), never silently skipped, but its documents cannot be
matched by số hiệu until that metadata is supplied.

doc_meta.json shape:
    { "van_ban_so_hieu": "30/2020/NĐ-CP", "van_ban_ten": "Nghị định ..." }

Each Điều entry in the catalog also carries its "khoan" list verbatim from
the source index.json (line-anchored heading text, no diem-file split) --
downstream consumers like legal-form-filler's checklist_from_catalog.py use
this to extract a hồ sơ/document checklist from a real Điều's enumerated
Khoản list, instead of a caller having to hand-type one with no source.

Usage:
    python build_catalog.py <corpus_root_dir> [-o catalog.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DIEU_NUMBER_RE = re.compile(r"^Đi[eề]u\s+(\d+)\b")

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def load_index(index_path: Path) -> dict | None:
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"SKIPPED {index_path.parent}: unreadable index.json ({exc})", file=sys.stderr)
        return None
    if data.get("structure_mode") != "legal":
        print(f"SKIPPED {index_path.parent}: index.json is not legal-article-mode output (structure_mode != 'legal')", file=sys.stderr)
        return None
    return data


def load_doc_meta(folder: Path) -> dict:
    meta_path = folder / "doc_meta.json"
    if not meta_path.exists():
        return {"van_ban_so_hieu": None, "van_ban_ten": None}
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"WARNING {meta_path}: unreadable doc_meta.json, ignoring ({exc})", file=sys.stderr)
        return {"van_ban_so_hieu": None, "van_ban_ten": None}
    return {
        "van_ban_so_hieu": data.get("van_ban_so_hieu"),
        "van_ban_ten": data.get("van_ban_ten"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("corpus_root", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()

    if not args.corpus_root.is_dir():
        print(f"Not a directory: {args.corpus_root}", file=sys.stderr)
        return 1

    documents = []
    for index_path in sorted(args.corpus_root.glob("*/index.json")):
        folder = index_path.parent
        index = load_index(index_path)
        if index is None:
            continue
        meta = load_doc_meta(folder)
        dieu = []
        for s in index.get("sections", []):
            m = DIEU_NUMBER_RE.match(s["heading"])
            dieu.append(
                {
                    "number": int(m.group(1)) if m else None,
                    "heading": s["heading"],
                    "file": s["file"],
                    "khoan": s.get("khoan", []),
                }
            )
        unparsed = [d["heading"] for d in dieu if d["number"] is None]
        if unparsed:
            print(f"WARNING {folder}: {len(unparsed)} section heading(s) didn't parse as 'Điều N' -- {unparsed}", file=sys.stderr)
        documents.append(
            {
                "folder": folder.name,
                "source_file": index.get("source_file"),
                "van_ban_so_hieu": meta["van_ban_so_hieu"],
                "van_ban_ten": meta["van_ban_ten"],
                "dieu": dieu,
            }
        )

    if not documents:
        print(f"No legal-article-mode index.json found under {args.corpus_root} (looked for */index.json)", file=sys.stderr)
        return 1

    undeclared = [d["folder"] for d in documents if not d["van_ban_so_hieu"]]

    catalog = {
        "corpus_root": str(args.corpus_root),
        "documents": documents,
    }

    out = json.dumps(catalog, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"OK: {len(documents)} document(s) -> {args.output}", file=sys.stderr)
    else:
        print(out)

    if undeclared:
        print(
            f"NOTE: {len(undeclared)} document(s) have no doc_meta.json (van_ban_so_hieu undeclared), "
            f"included by folder name only, cannot be matched by citation lookup yet: {undeclared}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
