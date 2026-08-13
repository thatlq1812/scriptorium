#!/usr/bin/env python3
"""Lint a TA's rubric-based grading run for one class against a validated
rubric: hard-refuse any criterion score exceeding its declared max (never
clamped -- same discipline as grading-and-feedback's own
essay/rubric-scoring rule, reused here rather than re-derived), then run a
cross-student statistical consistency pass that WARNS (does not block) on
patterns worth a human double-check.

Stdlib only (json, argparse, statistics). No AI/LLM/network call of any
kind -- this never judges whether a score is pedagogically correct, only
whether the grading run is internally consistent.

Hard errors (exit 1, block; a criterion score is NEVER silently clamped or
dropped):
  - a score for a criterion not declared in the rubric ("unknown criterion")
  - a score exceeding its criterion's max_points
  - a negative score
  - a duplicate student_id
  - a student with zero scores recorded

Warnings (printed, do not block exit 0) -- the statistical outlier layer:
  - a criterion scored for exactly 1 of N>=3 students (isolated usage --
    possible rubric-version drift or a data-entry slip)
  - a per-criterion Tukey IQR outlier: for a criterion scored by >=4
    students, any score falling outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR] is
    flagged. This is the standard box-plot outlier fence, not an invented
    threshold -- see John W. Tukey, "Exploratory Data Analysis" (1977), and
    NIST/SEMATECH e-Handbook of Statistical Methods §7.1.6
    (https://www.itl.nist.gov/div898/handbook/prc/section1/prc16.htm) for
    the same 1.5xIQR convention.
  - a student whose per-criterion scores have zero variance (identical
    score on every criterion they were graded on, min 3 criteria) while the
    class as a whole shows real variance on those same criteria --
    a "flatline" pattern worth a human double-check, per the general
    rubric-grading calibration/norming practice documented in Stevens &
    Levi, "Introduction to Rubrics" (2013) and widely-published university
    teaching-center rubric-calibration guides, which recommend spot-checking
    for graders/scores that show no discrimination across criteria.

Usage:
    python lint_grading_run.py rubric.json grading_run.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


class LintError(Exception):
    pass


def load_json(path: Path, label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LintError(f"cannot read {label}: {exc}") from exc
    if not isinstance(data, dict):
        raise LintError(f"top-level {label} JSON must be an object")
    return data


def load_rubric_criteria(rubric: dict) -> dict[str, float]:
    criteria = rubric.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise LintError("rubric.json: 'criteria' must be a non-empty list")
    max_points_by_name: dict[str, float] = {}
    for i, c in enumerate(criteria):
        if not isinstance(c, dict) or not c.get("name"):
            raise LintError(f"rubric.json: criteria[{i}] missing 'name'")
        max_points = c.get("max_points")
        if not isinstance(max_points, (int, float)) or isinstance(max_points, bool) or max_points <= 0:
            raise LintError(f"rubric.json: criteria[{i}] ({c['name']!r}) missing/invalid 'max_points'")
        max_points_by_name[c["name"]] = max_points
    return max_points_by_name


def hard_check(students: list, max_points_by_name: dict[str, float]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    for i, s in enumerate(students):
        if not isinstance(s, dict) or not s.get("student_id"):
            errors.append(f"students[{i}]: 'student_id' is required")
            continue
        sid = s["student_id"]
        if sid in seen_ids:
            errors.append(f"students[{i}]: duplicate student_id {sid!r}")
        seen_ids.add(sid)

        scores = s.get("scores")
        if not isinstance(scores, dict) or not scores:
            errors.append(f"student {sid!r}: 'scores' must be a non-empty object")
            continue

        for crit_name, score in scores.items():
            if crit_name not in max_points_by_name:
                errors.append(f"student {sid!r}: unknown criterion {crit_name!r} -- not declared in rubric.json")
                continue
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                errors.append(f"student {sid!r}, criterion {crit_name!r}: score must be a number, got {score!r}")
                continue
            if score < 0:
                errors.append(f"student {sid!r}, criterion {crit_name!r}: score {score!r} is negative")
                continue
            max_points = max_points_by_name[crit_name]
            if score > max_points:
                errors.append(
                    f"student {sid!r}, criterion {crit_name!r}: score {score!r} exceeds declared max_points "
                    f"{max_points!r} -- refused, never clamped"
                )

    return errors


def statistical_warnings(students: list, max_points_by_name: dict[str, float]) -> list[str]:
    warnings: list[str] = []
    n_students = len(students)

    scores_by_criterion: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for s in students:
        sid = s["student_id"]
        for crit_name, score in s["scores"].items():
            if crit_name in max_points_by_name:
                scores_by_criterion[crit_name].append((sid, score))

    # 1. Isolated-criterion-usage warning.
    if n_students >= 3:
        for crit_name, entries in scores_by_criterion.items():
            if len(entries) == 1:
                sid = entries[0][0]
                warnings.append(
                    f"criterion {crit_name!r} was scored for only 1 of {n_students} students "
                    f"(student {sid!r}) -- possible rubric-version drift or data-entry slip, verify"
                )

    # 2. Tukey 1.5xIQR outlier fence per criterion (needs >=4 data points for
    #    quartiles to be meaningful).
    for crit_name, entries in scores_by_criterion.items():
        if len(entries) < 4:
            continue
        values = sorted(v for _, v in entries)
        q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        for sid, v in entries:
            if v < lower_fence or v > upper_fence:
                warnings.append(
                    f"student {sid!r}, criterion {crit_name!r}: score {v!r} is a Tukey-IQR outlier "
                    f"(fences [{lower_fence!r}, {upper_fence!r}], Q1={q1!r}, Q3={q3!r}) -- worth a human double-check"
                )

    # 3. Flatline pattern: a student with zero variance across >=3 criteria
    #    they were scored on, where the class shows real variance on that
    #    same criterion set.
    for s in students:
        sid = s["student_id"]
        student_scores = {k: v for k, v in s["scores"].items() if k in max_points_by_name}
        if len(student_scores) < 3:
            continue
        values = list(student_scores.values())
        if statistics.pstdev(values) != 0:
            continue
        class_has_variance = False
        for crit_name in student_scores:
            entries = scores_by_criterion[crit_name]
            if len(entries) >= 2 and statistics.pstdev(v for _, v in entries) > 0:
                class_has_variance = True
                break
        if class_has_variance:
            warnings.append(
                f"student {sid!r}: identical score ({values[0]!r}) on all {len(values)} criteria they were "
                f"graded on, while the class shows variance on those criteria -- flatline pattern, worth a "
                f"human double-check"
            )

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rubric", type=Path, help="Path to a validated rubric JSON file")
    parser.add_argument("grading_run", type=Path, help="Path to a grading run JSON file (see assets/grading_run_template.json)")
    args = parser.parse_args()

    try:
        rubric = load_json(args.rubric, "rubric.json")
        max_points_by_name = load_rubric_criteria(rubric)
        grading_run = load_json(args.grading_run, "grading_run.json")
    except LintError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    students = grading_run.get("students")
    if not isinstance(students, list) or not students:
        print("MALFORMED: grading_run.json: 'students' must be a non-empty list", file=sys.stderr)
        return 2

    errors = hard_check(students, max_points_by_name)
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    warnings = statistical_warnings(students, max_points_by_name)
    print(f"VALID: {len(students)} students graded against rubric {rubric.get('rubric_id')!r}, "
          f"no criterion exceeded its max, no negative/unknown-criterion scores.")
    if warnings:
        print(f"WARNING: {len(warnings)} statistical consistency flag(s) -- not blocking, review before finalizing:")
        for w in warnings:
            print(f"  - {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
