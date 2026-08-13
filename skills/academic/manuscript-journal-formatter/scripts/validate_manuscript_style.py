#!/usr/bin/env python3
"""Validate a manuscript body's in-text citation format and its declared
reference list's format, both against a caller-declared citation style
(IEEE or APA 7th edition). Stdlib only (re, json, argparse), local,
deterministic -- no AI/LLM/network call of any kind, and this script never
rewrites the manuscript or the reference list itself.

Why this exists: citation-management (this repo's existing DOI/PMID/arXiv
-> BibTeX resolver) explicitly documents that it "doesn't validate citation
STYLE consistency across a whole bibliography (APA vs Vancouver etc.)" --
that is exactly the gap this skill closes, applied to a manuscript's BODY
text (in-text markers + reference list), not bibliography generation.

Two real, publicly documented styles are encoded, each cited to its actual
style guide (never invented):

- IEEE: numbered bracketed in-text citations ("[1]", "[1]-[3]", "[1], [2]"),
  reference list numbered sequentially in the order the entries are listed,
  each entry beginning with "[n]". Source: IEEE Editorial Style Manual for
  Authors (https://ieeeauthorcenter.ieee.org/wp-content/uploads/IEEE-Editorial-Style-Manual-for-Authors.pdf)
  and the IEEE Reference Guide
  (https://journals.ieeeauthorcenter.ieee.org/wp-content/uploads/sites/7/IEEE_Reference_Guide.pdf).
- APA (7th edition): parenthetical or narrative name-year in-text citations
  ("(Smith, 2021)" / "Smith (2021)"), reference list entries sorted
  alphabetically by first author's surname, each entry carrying a "(Year)".
  Source: APA Publication Manual, 7th ed., Chapter 8 (in-text citation) and
  Chapter 9/10 (reference list, alphabetical order,
  https://apastyle.apa.org/style-grammar-guidelines/citations).

Exit codes: 0 = valid, 1 = validation errors found, 2 = malformed input.

Usage:
    python validate_manuscript_style.py --style ieee|apa <manuscript.txt> <references.json>
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

IEEE_BRACKET_RE = re.compile(r"\[([0-9](?:[0-9,\-\s]*[0-9])?)\]")
APA_NAME_YEAR_PARENTHETICAL_RE = re.compile(
    r"\(([A-Z][A-Za-z\-']+(?:\s+(?:&|and)\s+[A-Z][A-Za-z\-']+)?(?:\s+et al\.)?,\s*(\d{4}[a-z]?))\)"
)
APA_NAME_YEAR_NARRATIVE_RE = re.compile(
    r"\b([A-Z][A-Za-z\-']+(?:\s+(?:&|and)\s+[A-Z][A-Za-z\-']+)?(?:\s+et al\.)?)\s+\((\d{4}[a-z]?)\)"
)
APA_SUSPECT_BRACKET_RE = re.compile(r"\[\d+\]")
IEEE_SUSPECT_NAME_YEAR_RE = re.compile(r"\([A-Z][A-Za-z\-']+,\s*\d{4}[a-z]?\)")


class ManuscriptError(Exception):
    pass


def load_references(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManuscriptError(f"cannot read references file: {exc}") from exc
    if not isinstance(data, dict):
        raise ManuscriptError("references.json top-level must be an object")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ManuscriptError("references.json must have a non-empty 'entries' list")
    return entries


def load_manuscript(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManuscriptError(f"cannot read manuscript file: {exc}") from exc


def expand_ieee_numbers(raw: str) -> list[int]:
    """Expand a bracket body like '1', '1, 2', or '1-3' into a list of ints."""
    numbers: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if "-" in part:
            lo_s, _, hi_s = part.partition("-")
            lo_s, hi_s = lo_s.strip(), hi_s.strip()
            if not lo_s.isdigit() or not hi_s.isdigit():
                continue
            lo, hi = int(lo_s), int(hi_s)
            if lo <= hi:
                numbers.extend(range(lo, hi + 1))
        elif part.isdigit():
            numbers.append(int(part))
    return numbers


def validate_ieee(manuscript: str, entries: list[dict]) -> list[str]:
    errors: list[str] = []

    # --- reference list checks ---
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict) or not entry.get("key"):
            errors.append(f"entries[{i}] must be an object with a non-empty 'key'")
            continue
        if entry["key"] != str(i + 1):
            errors.append(
                f"entries[{i}]: key {entry['key']!r} is not sequential -- IEEE reference lists must be "
                f"numbered '[1]', '[2]', ... in list order with no gaps or reordering (expected {i + 1!r})"
            )
        if not entry.get("authors"):
            errors.append(f"entries[{i}] (key {entry.get('key')!r}): 'authors' is required")
        if not entry.get("title"):
            errors.append(f"entries[{i}] (key {entry.get('key')!r}): 'title' is required")

    valid_numbers = {i + 1 for i in range(len(entries))}

    # --- in-text checks ---
    cited_numbers: set[int] = set()
    for m in IEEE_BRACKET_RE.finditer(manuscript):
        nums = expand_ieee_numbers(m.group(1))
        if not nums:
            errors.append(f"in-text citation {m.group(0)!r} could not be parsed as IEEE bracket-number form")
            continue
        for n in nums:
            cited_numbers.add(n)
            if n not in valid_numbers:
                errors.append(
                    f"in-text citation [{n}] has no matching reference-list entry (valid range is "
                    f"1-{len(entries)}) -- likely a fabricated or mistyped citation number"
                )

    if not cited_numbers and IEEE_BRACKET_RE.search(manuscript) is None:
        errors.append("no IEEE-style bracket-number in-text citations found in the manuscript")

    for suspect in IEEE_SUSPECT_NAME_YEAR_RE.finditer(manuscript):
        errors.append(
            f"in-text citation {suspect.group(0)!r} looks like name-year (APA-style) format, not IEEE "
            f"bracket-number form"
        )

    uncited = valid_numbers - cited_numbers
    if uncited:
        errors.append(f"reference list entry(ies) never cited in-text: {sorted(uncited)}")

    return errors


def validate_apa(manuscript: str, entries: list[dict]) -> list[str]:
    errors: list[str] = []

    surname_years: list[tuple[str, str]] = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict) or not entry.get("surname") or not entry.get("year"):
            errors.append(f"entries[{i}] must be an object with non-empty 'surname' and 'year'")
            continue
        if not entry.get("title"):
            errors.append(f"entries[{i}] ({entry.get('surname')!r}, {entry.get('year')!r}): 'title' is required")
        surname_years.append((str(entry["surname"]), str(entry["year"])))

    # alphabetical-order check (case-insensitive by surname)
    lowered = [s.lower() for s, _ in surname_years]
    if lowered != sorted(lowered):
        errors.append(
            "reference list is not sorted alphabetically by first-author surname -- APA 7th ed. requires "
            "alphabetical order (Ch. 9/10)"
        )

    # duplicate surname+year without a/b/c disambiguation suffix
    seen: dict[tuple[str, str], int] = {}
    for surname, year in surname_years:
        base_year = year.rstrip("abcdefghijklmnopqrstuvwxyz")
        key = (surname.lower(), base_year)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1 and year == base_year:
            errors.append(
                f"duplicate author-year {surname!r} {base_year!r} in reference list without an a/b/c "
                f"disambiguation suffix (APA 7th ed. §9.42)"
            )

    valid_pairs = {(s.lower(), y) for s, y in surname_years}
    valid_pairs_base = {(s.lower(), y.rstrip("abcdefghijklmnopqrstuvwxyz")) for s, y in surname_years}

    cited_pairs: set[tuple[str, str]] = set()

    for m in APA_NAME_YEAR_PARENTHETICAL_RE.finditer(manuscript):
        full, year = m.group(1), m.group(2)
        surname = full.split(",")[0].split(" and ")[0].split(" & ")[0].split(" et al.")[0].strip()
        pair = (surname.lower(), year)
        cited_pairs.add((surname.lower(), year.rstrip("abcdefghijklmnopqrstuvwxyz")))
        if pair not in valid_pairs and (surname.lower(), year.rstrip("abcdefghijklmnopqrstuvwxyz")) not in valid_pairs_base:
            errors.append(
                f"in-text citation '({full})' has no matching reference-list entry -- likely a fabricated "
                f"or mistyped citation"
            )

    for m in APA_NAME_YEAR_NARRATIVE_RE.finditer(manuscript):
        surname, year = m.group(1), m.group(2)
        surname_first = surname.split(" and ")[0].split(" & ")[0].split(" et al.")[0].strip()
        pair = (surname_first.lower(), year)
        cited_pairs.add((surname_first.lower(), year.rstrip("abcdefghijklmnopqrstuvwxyz")))
        if pair not in valid_pairs and (surname_first.lower(), year.rstrip("abcdefghijklmnopqrstuvwxyz")) not in valid_pairs_base:
            errors.append(
                f"in-text citation '{surname} ({year})' has no matching reference-list entry -- likely a "
                f"fabricated or mistyped citation"
            )

    if not cited_pairs:
        errors.append("no APA-style name-year in-text citations found in the manuscript")

    for suspect in APA_SUSPECT_BRACKET_RE.finditer(manuscript):
        errors.append(
            f"in-text citation {suspect.group(0)!r} looks like IEEE-style bracket-number form, not APA "
            f"name-year form"
        )

    uncited_pairs_base = {(s.lower(), y.rstrip("abcdefghijklmnopqrstuvwxyz")) for s, y in surname_years} - cited_pairs
    if uncited_pairs_base:
        errors.append(
            f"reference list entry(ies) never cited in-text: {sorted(uncited_pairs_base)}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--style", required=True, choices=["ieee", "apa"], help="Declared citation style")
    parser.add_argument("manuscript", type=Path, help="Path to a manuscript text/markdown file")
    parser.add_argument("references", type=Path, help="Path to a references JSON file (see assets/)")
    args = parser.parse_args()

    try:
        entries = load_references(args.references)
    except ManuscriptError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    try:
        manuscript = load_manuscript(args.manuscript)
    except ManuscriptError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if args.style == "ieee":
        errors = validate_ieee(manuscript, entries)
    else:
        errors = validate_apa(manuscript, entries)

    if errors:
        print(f"INVALID ({args.style.upper()}): {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        f"VALID ({args.style.upper()}): in-text citation format and reference-list format are internally "
        f"consistent with the declared style. This confirms formatting/consistency only, not that a cited "
        f"source's content actually supports the claim made about it."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
