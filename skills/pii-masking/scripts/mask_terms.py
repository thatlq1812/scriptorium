#!/usr/bin/env python3
"""Mechanically mask an agent/human-approved list of sensitive terms in a
text file, replacing every exact occurrence with a stable placeholder code
and writing a LOCAL-ONLY reversible mapping file.

This does no detection itself -- it trusts terms.json completely. Terms
come from either scan_sensitive_patterns.py's reviewed output (the
"match" field of approved findings) or explicit values the caller declares
(personal names, addresses -- anything with no reliable regex, same
discipline as grading-and-feedback/anonymize_roster.py's roster.json).

terms.json shape:
    { "terms": ["Nguyễn Văn A", "0912345678", "123456789012"] }

SENSITIVE / LOCAL-ONLY: the mapping file this writes (map.json by default)
contains the real term <-> placeholder-code correspondence. Never send this
file's contents to any LLM/network call or let it leave local storage --
only mask_terms.py and unmask.py read it, both entirely offline.

Exit codes: 0 = every declared term was found and masked at least once,
1 = masked output was still written but at least one declared term had
zero matches (check the report -- this usually means a typo or a Unicode
normalization mismatch, and a term you thought was masked may not be),
2 = malformed input / refused before writing anything.

Usage:
    python mask_terms.py <input_file> <terms.json> --out masked.md --map map.json [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def load_terms(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED terms.json: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict) or not isinstance(data.get("terms"), list):
        print("MALFORMED terms.json: must be an object with a 'terms' array.", file=sys.stderr)
        raise SystemExit(2)
    terms = [str(t) for t in data["terms"]]
    if not terms:
        print("terms.json 'terms' is empty -- nothing to mask.", file=sys.stderr)
        raise SystemExit(2)
    if len(set(terms)) != len(terms):
        seen = set()
        dupes = [t for t in terms if (t in seen) or seen.add(t)]
        print(f"MALFORMED terms.json: duplicate term(s): {dupes}", file=sys.stderr)
        raise SystemExit(2)
    if any(not t.strip() for t in terms):
        print("MALFORMED terms.json: a term is empty/blank.", file=sys.stderr)
        raise SystemExit(2)
    return terms


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("terms_json", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True, help="output mapping file path -- SENSITIVE, local-only")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Input not found: {args.input_file}", file=sys.stderr)
        return 1
    if not args.terms_json.exists():
        print(f"terms.json not found: {args.terms_json}", file=sys.stderr)
        return 1
    if (args.out.exists() or args.map.exists()) and not args.force:
        print(f"REFUSED: {args.out} or {args.map} already exists, use --force to overwrite", file=sys.stderr)
        return 2

    terms = load_terms(args.terms_json)
    text = args.input_file.read_text(encoding="utf-8")

    width = max(2, len(str(len(terms))))
    codes = [f"[PII_{str(i).zfill(width)}]" for i in range(1, len(terms) + 1)]
    term_to_code = dict(zip(terms, codes))

    # Replace longest terms first so a short term (e.g. "Văn A") can't eat
    # part of a longer overlapping term (e.g. "Nguyễn Văn A") before it's
    # matched, which would corrupt the longer term's count/replacement.
    masked = text
    counts: dict[str, int] = {}
    for term in sorted(terms, key=len, reverse=True):
        counts[term] = masked.count(term)
        masked = masked.replace(term, term_to_code[term])

    zero_matches = [t for t in terms if counts[t] == 0]

    # newline="\n" pins output to LF regardless of platform -- otherwise
    # Python's default text-mode write on Windows converts \n to \r\n,
    # which breaks byte-for-byte round-trip fidelity with unmask.py.
    args.out.write_text(masked, encoding="utf-8", newline="\n")
    mapping = {
        "_sensitive": "LOCAL-ONLY. Do not send this file's contents to any LLM/network call.",
        "source_file": str(args.input_file.name),
        "terms": [{"code": code, "value": term} for term, code in zip(terms, codes)],
    }
    args.map.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: wrote {args.out} and {args.map}")
    for term, code in zip(terms, codes):
        print(f"  {code}: {counts[term]} occurrence(s) masked")

    if zero_matches:
        print("", file=sys.stderr)
        print(f"WARNING: {len(zero_matches)} term(s) had ZERO matches -- not actually masked, check for typos:", file=sys.stderr)
        for t in zero_matches:
            nfc = unicodedata.normalize("NFC", t)
            nfd = unicodedata.normalize("NFD", t)
            variant_hint = ""
            if nfc in text or nfd in text:
                variant_hint = " (a different Unicode normalization form of this term WAS found in the text -- likely NFC/NFD mismatch)"
            print(f"  - {t!r}{variant_hint}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
