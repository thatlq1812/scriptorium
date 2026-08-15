#!/usr/bin/env python3
"""Validate a batch/tabular contract review: N documents reviewed against
the same M caller-declared review columns (e.g. a due-diligence checklist
applied across several contracts at once). Stdlib only (json, argparse),
local, deterministic -- no AI/network call of any kind.

Adapted from a recurring pattern found independently in 3 outside LegalTech
skill repos surveyed this session (claude-for-legal's tabular-review/
claim-chart, lq-skills' case-file-analyzer): every document x column cell
must be one of exactly 3 states -- a real value (with a verbatim quote +
location, never just an extracted claim with nothing to check it against),
"not_present" (the column genuinely doesn't apply to this document), or
"needs_review" (a human must look again, with a stated reason). A missing
cell is never silently treated as "not present" -- every declared
document x column pair must have an explicit cell, or this refuses.

This is a GENERIC schema, not one elicited from a real thatlq1812-supplied
diligence checklist (none was available) -- the caller declares whatever
columns/documents apply to their own real review. Same non-detection
posture as validate_risk_log.py: this never decides whether a clause is
risky or what a cell's value should be, only that a human/agent-authored
batch review is structurally complete, grounded (quote + location), and
never silently ambiguous about what wasn't checked.

Exit codes: 0 = structurally valid, 1 = errors found, 2 = malformed input.

Usage:
    python batch_tabular_review.py batch_review.json [--render batch_review.md] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_STATES = {"value", "not_present", "needs_review"}


def validate(review: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("review_title", "reviewer", "review_date"):
        if not review.get(field):
            errors.append(f"{field} is required")

    documents = review.get("documents")
    if not isinstance(documents, list) or not documents or not all(isinstance(d, str) and d.strip() for d in documents):
        errors.append("documents must be a non-empty list of non-empty strings")
        documents = []
    elif len(set(documents)) != len(documents):
        errors.append("documents contains a duplicate entry")

    columns = review.get("columns")
    if not isinstance(columns, list) or not columns or not all(isinstance(c, str) and c.strip() for c in columns):
        errors.append("columns must be a non-empty list of non-empty strings")
        columns = []
    elif len(set(columns)) != len(columns):
        errors.append("columns contains a duplicate entry")

    cells = review.get("cells")
    if not isinstance(cells, list):
        errors.append("cells must be a list")
        return errors, warnings

    if not documents or not columns:
        return errors, warnings  # can't cross-check coverage without both axes

    expected = {(d, c) for d in documents for c in columns}
    seen: set[tuple[str, str]] = set()

    for i, cell in enumerate(cells):
        if not isinstance(cell, dict):
            errors.append(f"cells[{i}] must be an object")
            continue

        doc = cell.get("document")
        col = cell.get("column")
        if doc not in documents:
            errors.append(f"cells[{i}]: document {doc!r} is not in the declared documents list")
            continue
        if col not in columns:
            errors.append(f"cells[{i}]: column {col!r} is not in the declared columns list")
            continue

        key = (doc, col)
        if key in seen:
            errors.append(f"cells[{i}]: duplicate cell for document={doc!r}, column={col!r}")
        seen.add(key)

        state = cell.get("state")
        if state not in VALID_STATES:
            errors.append(f"cells[{i}] ({doc!r}/{col!r}): state must be one of {sorted(VALID_STATES)}, got {state!r}")
            continue

        if state == "value":
            if not cell.get("value"):
                errors.append(f"cells[{i}] ({doc!r}/{col!r}): state='value' requires a non-empty 'value'")
            if not cell.get("verbatim_quote"):
                errors.append(
                    f"cells[{i}] ({doc!r}/{col!r}): state='value' requires a non-empty 'verbatim_quote' -- "
                    f"a value with nothing to check it against is an unverifiable claim, not a finding"
                )
            if not cell.get("location"):
                errors.append(f"cells[{i}] ({doc!r}/{col!r}): state='value' requires a non-empty 'location' (e.g. 'Điều 5')")
        elif state == "needs_review":
            if not cell.get("note"):
                errors.append(
                    f"cells[{i}] ({doc!r}/{col!r}): state='needs_review' requires a non-empty 'note' explaining "
                    f"why (e.g. illegible, ambiguous, conflicting) -- 'needs review' with no reason is not actionable"
                )

    missing = expected - seen
    for doc, col in sorted(missing):
        errors.append(f"missing cell: document={doc!r}, column={col!r} -- every document x column pair must have an explicit cell, never silently blank")

    return errors, warnings


def to_markdown(review: dict) -> str:
    documents = review["documents"]
    columns = review["columns"]
    cell_by_key = {(c["document"], c["column"]): c for c in review.get("cells", []) if isinstance(c, dict)}

    lines = [
        f"# Batch Tabular Review: {review['review_title']}",
        "",
        f"**Reviewer**: {review['reviewer']} | **Date**: {review['review_date']}",
        "",
        "| Document | " + " | ".join(columns) + " |",
        "| --- | " + " | ".join("---" for _ in columns) + " |",
    ]
    for doc in documents:
        row = [doc]
        for col in columns:
            cell = cell_by_key.get((doc, col))
            if cell is None:
                row.append("?")
            elif cell["state"] == "value":
                row.append(f"{cell['value']} ({cell['location']})")
            elif cell["state"] == "not_present":
                row.append("_không có_")
            else:
                row.append(f"_cần rà soát lại: {cell.get('note', '')}_")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("batch_review", type=Path, help="Path to a batch review JSON file (see assets/batch_tabular_review_template.json)")
    parser.add_argument("--render", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        review = json.loads(args.batch_review.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(review, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = validate(review)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        f"VALID: {len(review['documents'])} document(s) x {len(review['columns'])} column(s), "
        f"every cell present and grounded. This confirms structure only, not the correctness of any cell's content."
    )

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(review), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
