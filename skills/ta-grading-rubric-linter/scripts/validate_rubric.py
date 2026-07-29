#!/usr/bin/env python3
"""Validate a TA rubric definition JSON: every criterion has a positive
max_points, criterion names are unique, and the sum of all criteria's
max_points equals the declared total_points. Stdlib only (json, argparse),
local, deterministic -- no AI/LLM/network call of any kind.

Mirrors competency-rubric-builder's "weights must sum to the declared
scale" invariant, applied here to a flat TA grading rubric (criterion ->
max_points) rather than a criteria x performance-level matrix.

Exit codes: 0 = valid, 1 = validation errors found, 2 = malformed input.

Usage:
    python validate_rubric.py rubric.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


class RubricError(Exception):
    pass


def load_rubric(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RubricError(f"cannot read rubric file: {exc}") from exc
    if not isinstance(data, dict):
        raise RubricError("top-level rubric JSON must be an object")
    return data


def validate(rubric: dict) -> list[str]:
    errors: list[str] = []

    if not rubric.get("rubric_id"):
        errors.append("rubric_id is required")

    total_points = rubric.get("total_points")
    if not isinstance(total_points, (int, float)) or isinstance(total_points, bool) or total_points <= 0:
        errors.append("total_points is required and must be a positive number")
        total_points = None

    criteria = rubric.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        errors.append("criteria must be a non-empty list")
        return errors

    seen_names: set[str] = set()
    running_sum = 0.0
    sum_valid = True
    for i, c in enumerate(criteria):
        if not isinstance(c, dict) or not c.get("name"):
            errors.append(f"criteria[{i}]: 'name' is required")
            sum_valid = False
            continue
        name = c["name"]
        if name in seen_names:
            errors.append(f"criteria[{i}]: duplicate criterion name {name!r}")
        seen_names.add(name)
        max_points = c.get("max_points")
        if not isinstance(max_points, (int, float)) or isinstance(max_points, bool) or max_points <= 0:
            errors.append(f"criteria[{i}] ({name!r}): max_points is required and must be a positive number")
            sum_valid = False
            continue
        running_sum += max_points

    if sum_valid and total_points is not None and abs(running_sum - total_points) > 1e-9:
        errors.append(
            f"criteria max_points sum to {running_sum!r} but rubric declares total_points={total_points!r} "
            f"(off by {running_sum - total_points!r})"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rubric", type=Path, help="Path to a rubric JSON file (see assets/rubric_template.json)")
    args = parser.parse_args()

    try:
        rubric = load_rubric(args.rubric)
    except RubricError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    errors = validate(rubric)
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"VALID: rubric {rubric.get('rubric_id')!r} is structurally sound "
          f"({len(rubric['criteria'])} criteria summing to {rubric['total_points']}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
