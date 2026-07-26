#!/usr/bin/env python3
"""Lint a batch of qualitative student remarks for level-appropriate
assessment language — stdlib only, local, deterministic. No LLM/AI call.

Reuses the exact scoring-language check already proven in
lesson-plan-builder/scripts/validate_lesson_plan.py's SCORE_LANGUAGE_RE and
its TH-vs-THCS/THPT level branching:

  - grade_level 1-5 (Tiểu học): TT 27/2020 forbids numeric/scoring language
    ("cho điểm"/"chấm điểm"/"điểm số") and a bare numeric grade pattern
    (e.g. "8/10", "9 điểm", "điểm: 7") in a regular-lesson remark. A remark
    that contains any of this is a hard ERROR.
  - grade_level 6-12 (THCS/THPT): TT 22/2021 allows scoring language — no
    restriction is applied.

Also checks, regardless of level:
  - empty/placeholder remarks (still holding a `<...>` template placeholder,
    or blank/whitespace-only) — hard ERROR.
  - near-duplicate remarks reused verbatim across many different students —
    a real quality smell (templated, not individualized feedback) — soft
    WARNING, not a hard error, since a short generic sentence can
    legitimately repeat by coincidence for a couple of students.

This checks LANGUAGE, not truth or pedagogical quality — it cannot verify
whether a remark is actually accurate or well-observed.

Usage:
    python lint_remarks.py <remarks.json>

Exit codes: 0 = clean (warnings may still print), 1 = errors found,
2 = malformed input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

# Identical pattern to lesson-plan-builder/scripts/validate_lesson_plan.py's
# SCORE_LANGUAGE_RE — kept in sync deliberately, this is proven-correct in
# this repo already.
SCORE_LANGUAGE_RE = re.compile(r"cho điểm|chấm điểm|điểm số", re.IGNORECASE)

# A bare numeric grade pattern: "8/10", "9 điểm", "điểm: 7", "7.5/10".
NUMERIC_GRADE_RE = re.compile(
    r"\b\d+([.,]\d+)?\s*/\s*\d+([.,]\d+)?\b"       # 8/10, 7.5/10
    r"|\b\d+([.,]\d+)?\s*điểm\b"                    # 9 điểm
    r"|\bđiểm\s*[:：]\s*\d+([.,]\d+)?\b",            # điểm: 7 (also matches "Điểm:")
    re.IGNORECASE,
)

PLACEHOLDER_RE = re.compile(r"^\s*<.*>\s*$", re.DOTALL)

DUPLICATE_WARN_THRESHOLD = 3  # >= this many identical remarks triggers a warning


def infer_cap(grade_level: int) -> str:
    if 1 <= grade_level <= 5:
        return "TH"
    if 6 <= grade_level <= 12:
        return "THCS_THPT"
    raise ValueError(f"grade_level must be 1-12, got {grade_level}")


def is_blank_or_placeholder(text: str) -> bool:
    if not text.strip():
        return True
    return bool(PLACEHOLDER_RE.match(text))


def lint(batch: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    grade_level = batch.get("grade_level")
    if not isinstance(grade_level, int):
        errors.append(f"grade_level must be an integer, got {grade_level!r}")
        return errors, warnings
    try:
        cap = infer_cap(grade_level)
    except ValueError as exc:
        errors.append(str(exc))
        return errors, warnings

    remarks = batch.get("remarks")
    if not isinstance(remarks, list) or not remarks:
        errors.append("'remarks' must be a non-empty list")
        return errors, warnings

    normalized_texts: list[str] = []
    seen_ids: set[str] = set()

    for i, item in enumerate(remarks):
        if not isinstance(item, dict):
            errors.append(f"remarks[{i}] must be an object")
            continue
        student_id = str(item.get("student_id", "")).strip()
        if not student_id:
            errors.append(f"remarks[{i}] missing 'student_id'")
            continue
        if student_id in seen_ids:
            errors.append(f"duplicate student_id: {student_id!r}")
            continue
        seen_ids.add(student_id)

        text = str(item.get("text", ""))

        if is_blank_or_placeholder(text):
            errors.append(f"{student_id}: remark is empty or still a template placeholder")
            continue

        if cap == "TH":
            if SCORE_LANGUAGE_RE.search(text):
                errors.append(
                    f"{student_id}: remark contains scoring language ('cho điểm'/'chấm điểm'/'điểm số') "
                    f"but grade_level {grade_level} implies cấp Tiểu học (TT27/2020: nhận xét only, no scores)"
                )
                continue
            if NUMERIC_GRADE_RE.search(text):
                errors.append(
                    f"{student_id}: remark contains a numeric-grade pattern (e.g. '8/10', '9 điểm') "
                    f"but grade_level {grade_level} implies cấp Tiểu học (TT27/2020: no scores in a regular-lesson remark)"
                )
                continue

        normalized_texts.append(" ".join(text.split()).strip().lower())

    # Soft quality signal: identical remark text reused across many students.
    counts = Counter(normalized_texts)
    for text, count in counts.items():
        if count >= DUPLICATE_WARN_THRESHOLD:
            preview = text[:80] + ("..." if len(text) > 80 else "")
            warnings.append(
                f"{count} students have the exact same remark text — looks templated, not individualized: {preview!r}"
            )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("remarks", type=Path, help="Path to a remarks-batch JSON file")
    args = parser.parse_args()

    try:
        batch = json.loads(args.remarks.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(batch, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = lint(batch)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: all remarks pass level-appropriate assessment-language checks. This confirms language rules only, not accuracy/quality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
