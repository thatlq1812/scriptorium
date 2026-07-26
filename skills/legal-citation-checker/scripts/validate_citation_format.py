#!/usr/bin/env python3
"""Validate the FORMAT of Vietnamese legal citations (Điều/Khoản/Điểm + văn
bản số hiệu) and check title consistency across repeated citations of the
same document. Stdlib only (re, json, argparse), local, deterministic --
no AI/network call of any kind.

CRITICAL SCOPE LIMIT (read before use): this script does NOT verify that a
cited legal document is currently in effect (hiệu lực), has been amended,
or has been repealed. No free, official Vietnamese legal-document database
or API exists for this project to query (unlike CrossRef for academic
DOIs) -- attempting to guess or assert a hiệu lực status without a real
source would be exactly the kind of fabrication this project's citation-
management skill was built to avoid. This script checks citation FORMAT
and INTERNAL CONSISTENCY only. Verifying a citation's real-world legal
status remains a human task (or a future version of this skill, if/when a
real queryable source is supplied).

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_citation_format.py citations.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

# Two known Vietnamese legal-document numbering conventions:
#   - With year (Nghị định/Thông tư/Quyết định/...): <so>/<nam>/<loai-co_quan>
#     e.g. "30/2020/NĐ-CP", "22/2021/TT-BGDĐT"
#   - Without year (Công văn/chỉ đạo): <so>/<co_quan>-<don_vi>
#     e.g. "5512/BGDĐT-GDTrH"
_SEGMENT = r"[A-ZĐ][A-Za-zĐđ]*"  # e.g. "NĐ", "TT", "BGDĐT", "GDTrH" (mixed-case agency abbreviations are real)
DOC_WITH_YEAR_RE = re.compile(rf"^\d{{1,6}}/\d{{4}}/{_SEGMENT}(-{_SEGMENT})*$")
DOC_WITHOUT_YEAR_RE = re.compile(rf"^\d{{1,6}}/{_SEGMENT}(-{_SEGMENT})*$")
DIEM_RE = re.compile(r"^[a-z]$")


class CitationError(Exception):
    pass


def validate_so_hieu(so_hieu: str) -> bool:
    return bool(DOC_WITH_YEAR_RE.match(so_hieu) or DOC_WITHOUT_YEAR_RE.match(so_hieu))


def validate(citations: list[dict]) -> list[str]:
    errors: list[str] = []
    title_by_so_hieu: dict[str, str] = {}

    for i, c in enumerate(citations):
        if not isinstance(c, dict):
            errors.append(f"citations[{i}] must be an object")
            continue

        dieu = c.get("dieu")
        if not isinstance(dieu, int) or dieu < 1:
            errors.append(f"citations[{i}]: dieu must be a positive integer, got {dieu!r}")

        khoan = c.get("khoan")
        if khoan is not None and (not isinstance(khoan, int) or khoan < 1):
            errors.append(f"citations[{i}]: khoan must be a positive integer or null, got {khoan!r}")

        diem = c.get("diem")
        if diem is not None and not DIEM_RE.match(str(diem)):
            errors.append(f"citations[{i}]: diem must be a single lowercase letter (a, b, c, ...) or null, got {diem!r}")

        so_hieu = c.get("van_ban_so_hieu")
        if not so_hieu:
            errors.append(f"citations[{i}]: van_ban_so_hieu is required")
        elif not validate_so_hieu(so_hieu):
            errors.append(
                f"citations[{i}]: van_ban_so_hieu {so_hieu!r} doesn't match a known Vietnamese legal-document "
                f"numbering convention (expected '<so>/<nam>/<loai>-<co_quan>' e.g. '30/2020/NĐ-CP', or "
                f"'<so>/<co_quan>-<don_vi>' e.g. '5512/BGDĐT-GDTrH')"
            )

        ten = c.get("van_ban_ten")
        if not ten:
            errors.append(f"citations[{i}]: van_ban_ten is required")
        elif so_hieu:
            if so_hieu in title_by_so_hieu and title_by_so_hieu[so_hieu] != ten:
                errors.append(
                    f"citations[{i}]: van_ban_so_hieu {so_hieu!r} is cited with title {ten!r} here, "
                    f"but title {title_by_so_hieu[so_hieu]!r} earlier -- same document cited with 2 different titles, likely one is wrong"
                )
            else:
                title_by_so_hieu[so_hieu] = ten

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("citations", type=Path, help="Path to a citations JSON file (see assets/citations_template.json)")
    args = parser.parse_args()

    try:
        data = json.loads(args.citations.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    citations = data.get("citations") if isinstance(data, dict) else None
    if not isinstance(citations, list) or not citations:
        print("MALFORMED: input must be an object with a non-empty 'citations' list", file=sys.stderr)
        return 2

    errors = validate(citations)

    print(
        "NOTE: this checks citation FORMAT and title consistency only -- it does NOT verify a document is "
        "currently in effect (hiệu lực). No free Vietnamese legal-document database is available to this "
        "project; verifying real-world legal status remains a human task.",
        file=sys.stderr,
    )

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {len(citations)} citation(s) well-formed, no title inconsistency found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
