#!/usr/bin/env python3
"""Extract a document checklist (check_dossier.py's required_documents
format) from a real Điều's enumerated Khoản list in a document-ai-structurer
catalog.json, instead of a caller hand-typing a checklist with no source.

This is mechanical extraction, not judgment: it takes every Khoản heading
text verbatim under the specified Điều/văn bản số hiệu and writes it as a
required_documents entry. It does NOT decide which Điều of which document
is the right hồ sơ/checklist provision for a given procedure -- that's the
same "form suggestion" domain judgment legal-form-filler already declares
out of scope (no real government checklist database exists to ground it
in). The caller (a human or the calling agent, having read the actual Điều
text) must already know this Điều enumerates required documents, not some
other kind of list (obligations, deadlines, penalties -- an Điều's Khoản
list is not always a checklist).

Stdlib only (json, argparse), local, deterministic -- no AI/network call.

Exit codes: 0 = extracted, 1 = Điều/document not found in catalog,
2 = malformed input.

Usage:
    python checklist_from_catalog.py <catalog.json> <van_ban_so_hieu> <dieu_number> [-o checklist.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("van_ban_so_hieu")
    parser.add_argument("dieu_number", type=int)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()

    if not args.catalog.exists():
        print(f"catalog not found: {args.catalog}", file=sys.stderr)
        return 1

    try:
        data = json.loads(args.catalog.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED catalog.json: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict) or not isinstance(data.get("documents"), list):
        print("MALFORMED catalog.json: must be an object with a 'documents' list", file=sys.stderr)
        return 2

    doc = next((d for d in data["documents"] if d.get("van_ban_so_hieu") == args.van_ban_so_hieu), None)
    if doc is None:
        known = sorted({d.get("van_ban_so_hieu") for d in data["documents"] if d.get("van_ban_so_hieu")})
        print(f"NOT FOUND: {args.van_ban_so_hieu!r} is not in this catalog. Known: {known}", file=sys.stderr)
        return 1

    dieu = next((d for d in doc.get("dieu", []) if d.get("number") == args.dieu_number), None)
    if dieu is None:
        known_nums = sorted(d["number"] for d in doc.get("dieu", []) if d.get("number") is not None)
        print(f"NOT FOUND: Điều {args.dieu_number} not in {args.van_ban_so_hieu!r}. Known Điều: {known_nums}", file=sys.stderr)
        return 1

    khoan = dieu.get("khoan", [])
    if not khoan:
        print(
            f"REFUSED: Điều {args.dieu_number} of {args.van_ban_so_hieu!r} ({dieu['heading']!r}) has no Khoản "
            "list in the catalog -- nothing to extract as a checklist.",
            file=sys.stderr,
        )
        return 1

    checklist = {
        "procedure_name": f"Extracted from {args.van_ban_so_hieu}, {dieu['heading']}",
        "required_documents": [k["heading"] for k in khoan],
        "_source": {
            "van_ban_so_hieu": args.van_ban_so_hieu,
            "van_ban_ten": doc.get("van_ban_ten"),
            "dieu_heading": dieu["heading"],
        },
    }

    out = json.dumps(checklist, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"OK: {len(khoan)} Khoản item(s) extracted -> {args.output}", file=sys.stderr)
    else:
        print(out)

    print(
        f"REMINDER: verify Điều {args.dieu_number} of {args.van_ban_so_hieu!r} actually enumerates a document "
        "checklist before using this output -- not every Khoản list is a hồ sơ requirement, and this script "
        "extracts whatever list is there verbatim without judging its content. Does not decide which Điều/document "
        "is the right one for a given procedure (out of scope, same as legal-form-filler's form-suggestion gap).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
