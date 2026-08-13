#!/usr/bin/env python3
"""Scan a text file for CANDIDATE sensitive-identifier patterns common in
Vietnamese documents (CCCD/CMND numbers, phone numbers, email addresses,
keyword-triggered digit runs like bank account / tax code / date of birth).

Regex + keyword-context only, stdlib, no network, no LLM call. This is a
candidate report, not an authority -- every match must be reviewed by the
agent/human before being fed to mask_terms.py, same two-step shape as
document-ai-structurer's suggest_legal_boundaries.py -> apply_legal_structure.py.

DOES NOT detect personal names, home addresses, or any free-text sensitive
value with no fixed pattern -- there is no reliable regex for a Vietnamese
name. The caller must declare those explicitly as extra terms when calling
mask_terms.py (same discipline as anonymize_roster.py's roster.json input).

Usage:
    python scan_sensitive_patterns.py <input_file> [-o findings.json]
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

CCCD_RE = re.compile(r"\b\d{12}\b")
CMND_RE = re.compile(r"\b\d{9}\b")
PHONE_RE = re.compile(r"(?:\+84|0)(?:3|5|7|8|9)\d{8}\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")

# Keyword -> if this keyword appears anywhere on the line, any digit run of
# 6-19 digits on that line is a candidate, even if it doesn't match a fixed
# pattern above (bank accounts, tax codes, insurance numbers have no single
# universal format).
KEYWORD_DIGIT_TRIGGERS = [
    "số tài khoản", "stk", "mã số thuế", "số bảo hiểm", "hộ chiếu",
    "passport", "số căn cước", "cccd", "cmnd", "ngày sinh", "sinh ngày",
]
DIGIT_RUN_RE = re.compile(r"\b\d{6,19}\b")


def scan_line(line_no: int, line: str) -> list[dict]:
    hits = []

    cccd_matches = list(CCCD_RE.finditer(line))
    for m in cccd_matches:
        hits.append({"type": "cccd_candidate", "line": line_no, "match": m.group(0), "context": line.strip()})
    cccd_spans = [(m.start(), m.end()) for m in cccd_matches]
    for m in CMND_RE.finditer(line):
        # skip a 9-digit run that's just a substring of an already-recorded 12-digit CCCD match
        if any(cs <= m.start() and m.end() <= ce for cs, ce in cccd_spans):
            continue
        hits.append({"type": "cmnd_candidate", "line": line_no, "match": m.group(0), "context": line.strip()})
    for m in PHONE_RE.finditer(line):
        hits.append({"type": "phone_candidate", "line": line_no, "match": m.group(0), "context": line.strip()})
    for m in EMAIL_RE.finditer(line):
        hits.append({"type": "email_candidate", "line": line_no, "match": m.group(0), "context": line.strip()})

    lower = line.lower()
    if any(kw in lower for kw in KEYWORD_DIGIT_TRIGGERS):
        for m in DIGIT_RUN_RE.finditer(line):
            already = any(h["match"] == m.group(0) and h["line"] == line_no for h in hits)
            if not already:
                hits.append({"type": "keyword_digit_candidate", "line": line_no, "match": m.group(0), "context": line.strip()})

    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None, help="write JSON here instead of stdout")
    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Input not found: {args.input_file}", file=sys.stderr)
        return 1

    lines = args.input_file.read_text(encoding="utf-8").split("\n")
    all_hits: list[dict] = []
    for i, line in enumerate(lines, start=1):
        all_hits.extend(scan_line(i, line))

    report = {
        "_warning": (
            "UNVERIFIED CANDIDATES -- regex/keyword heuristics only. Personal "
            "names and addresses are NOT detected here (no reliable pattern); "
            "declare them explicitly as extra terms when calling mask_terms.py. "
            "Review every match's 'context' before approving it for masking -- "
            "a 12-digit run is not always a CCCD number."
        ),
        "source_file": str(args.input_file.name),
        "findings": all_hits,
    }

    out = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"OK: {len(all_hits)} candidate(s) -> {args.output}", file=sys.stderr)
    else:
        print(out)

    print(f"Reminder: {len(all_hits)} candidates, review before masking -- see _warning field.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
