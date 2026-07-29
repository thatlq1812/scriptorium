#!/usr/bin/env python3
"""Aggregate and validate a child's report-card/progress data over time for
a parent/guardian: structural completeness of a multi-period record, and a
deterministic trend computation (per-subject and overall score deltas
across chronologically ordered periods). Stdlib only (json, argparse),
local, deterministic -- no AI/network of any kind.

This does NOT invent any grading/weighting logic. Per-subject and overall
trend deltas are plain arithmetic differences between consecutive periods
(later score minus earlier score) -- there is no invented "significance"
threshold, no invented official weighting scheme, and no invented
pass/fail classification. If a caller has a real official overall average
(e.g. an actual TBM from a report card), it goes in
'reported_overall_average' and is used as-is; if omitted, this script
computes a plain UNWEIGHTED mean of that period's subject_scores and
labels it explicitly as 'computed_unweighted_average', never presented as
an official average, mirroring grade-book-builder's refusal to assert
unverified official weighting numbers.

Checks (errors -- hard-block):
  - student_name non-empty string.
  - records: non-empty list.
  - Each record: period_label non-empty string, period_order a unique
    integer (used for chronological ordering -- explicit, never inferred
    from list position or date, since date is optional and this project
    does not guess ordering), subject_scores a non-empty object of
    subject -> number in [0, 10] (same 0-10 Vietnamese scale convention
    already documented and reused from grade-book-builder -- not a new
    invented meaning), date (if present) a valid ISO 'YYYY-MM-DD' string,
    reported_overall_average (if present, non-null) a number in [0, 10].
  - No duplicate period_order across records.

Checks (warnings -- non-blocking):
  - A subject present in some periods but not others (a student may add
    or drop a subject across years/terms -- this is informational, not an
    error).
  - Fewer than 2 records: trend cannot be computed; the result still
    validates, with an explicit note that trend fields are empty.

Exit codes: 0 = structurally valid (trend computed if >=2 records,
warnings may print), 1 = at least one structural error, 2 = file not
readable / malformed JSON, or an existing --render/--out target without
--force.

Usage:
    python track_progress.py records.json [--render summary.md] [--out result.json] [--force]
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

SCORE_MIN = 0.0
SCORE_MAX = 10.0
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _is_valid_iso_date(value: str) -> bool:
    if not ISO_DATE_RE.match(value):
        return False
    year, month, day = (int(p) for p in value.split("-"))
    if not (1 <= month <= 12):
        return False
    days_in_month = [31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= day <= days_in_month[month - 1]


def _direction(delta: float) -> str:
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "flat"


def validate_and_compute(data: dict) -> tuple[list[str], list[str], dict | None]:
    """Returns (errors, warnings, result). result is None if errors non-empty."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("student_name", "records"):
        if field not in data:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, warnings, None

    student_name = data["student_name"]
    if not isinstance(student_name, str) or not student_name.strip():
        errors.append("student_name must be a non-empty string")

    records = data["records"]
    if not isinstance(records, list) or not records:
        errors.append("records must be a non-empty list")
        return errors, warnings, None

    parsed_records: list[dict] = []
    seen_orders: list[int] = []

    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            errors.append(f"records[{i}] must be an object")
            continue

        for field in ("period_label", "period_order", "subject_scores"):
            if field not in rec:
                errors.append(f"records[{i}]: missing required field '{field}'")
        if any(f"records[{i}]:" in e for e in errors):
            continue

        period_label = rec["period_label"]
        if not isinstance(period_label, str) or not period_label.strip():
            errors.append(f"records[{i}].period_label must be a non-empty string")

        period_order = rec["period_order"]
        if not isinstance(period_order, int) or isinstance(period_order, bool):
            errors.append(f"records[{i}].period_order must be an integer, got {period_order!r}")
            continue
        seen_orders.append(period_order)

        date = rec.get("date")
        if date is not None:
            if not isinstance(date, str) or not _is_valid_iso_date(date):
                errors.append(f"records[{i}] (period_order={period_order}): date must be a valid ISO 'YYYY-MM-DD' string if present, got {date!r}")

        subject_scores = rec["subject_scores"]
        if not isinstance(subject_scores, dict) or not subject_scores:
            errors.append(f"records[{i}] (period_order={period_order}): subject_scores must be a non-empty object")
            continue

        parsed_scores: dict[str, float] = {}
        row_ok = True
        for subject, score in subject_scores.items():
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                errors.append(f"records[{i}] (period_order={period_order}): subject_scores[{subject!r}] must be a number, got {score!r}")
                row_ok = False
                continue
            if not (SCORE_MIN <= score <= SCORE_MAX):
                errors.append(f"records[{i}] (period_order={period_order}): subject_scores[{subject!r}] value {score!r} is outside the {SCORE_MIN}-{SCORE_MAX} scale")
                row_ok = False
                continue
            parsed_scores[subject] = float(score)
        if not row_ok:
            continue

        reported_overall = rec.get("reported_overall_average")
        if reported_overall is not None:
            if not isinstance(reported_overall, (int, float)) or isinstance(reported_overall, bool):
                errors.append(f"records[{i}] (period_order={period_order}): reported_overall_average must be a number if present, got {reported_overall!r}")
                continue
            if not (SCORE_MIN <= reported_overall <= SCORE_MAX):
                errors.append(f"records[{i}] (period_order={period_order}): reported_overall_average {reported_overall!r} is outside the {SCORE_MIN}-{SCORE_MAX} scale")
                continue
            reported_overall = float(reported_overall)

        computed_unweighted = sum(parsed_scores.values()) / len(parsed_scores)

        parsed_records.append({
            "period_label": period_label,
            "period_order": period_order,
            "date": date,
            "subject_scores": parsed_scores,
            "reported_overall_average": reported_overall,
            "computed_unweighted_average": round(computed_unweighted, 2),
            "overall_source": "reported" if reported_overall is not None else "computed_unweighted",
            "overall_value": reported_overall if reported_overall is not None else round(computed_unweighted, 2),
        })

    if len(set(seen_orders)) != len(seen_orders):
        dupes = sorted({o for o in seen_orders if seen_orders.count(o) > 1})
        errors.append(f"records have duplicate period_order value(s): {dupes}")

    if errors:
        return errors, warnings, None

    parsed_records.sort(key=lambda r: r["period_order"])

    all_subjects: set[str] = set()
    for r in parsed_records:
        all_subjects.update(r["subject_scores"].keys())
    for subject in sorted(all_subjects):
        missing_in = [r["period_label"] for r in parsed_records if subject not in r["subject_scores"]]
        if missing_in:
            warnings.append(f"subject {subject!r} is present in some periods but missing in: {missing_in} -- trend for this subject only compares periods where it appears")

    subject_trends: dict[str, dict] = {}
    for subject in sorted(all_subjects):
        points = [
            {"period_label": r["period_label"], "period_order": r["period_order"], "score": r["subject_scores"][subject]}
            for r in parsed_records if subject in r["subject_scores"]
        ]
        deltas = []
        for a, b in zip(points, points[1:]):
            delta = round(b["score"] - a["score"], 2)
            deltas.append({
                "from_period": a["period_label"],
                "to_period": b["period_label"],
                "delta": delta,
                "direction": _direction(delta),
            })
        overall_delta = None
        if len(points) >= 2:
            overall_delta = round(points[-1]["score"] - points[0]["score"], 2)
        subject_trends[subject] = {
            "points": points,
            "consecutive_deltas": deltas,
            "overall_delta_first_to_last": overall_delta,
            "overall_direction_first_to_last": _direction(overall_delta) if overall_delta is not None else None,
        }

    overall_points = [
        {"period_label": r["period_label"], "period_order": r["period_order"], "value": r["overall_value"], "source": r["overall_source"]}
        for r in parsed_records
    ]
    overall_deltas = []
    for a, b in zip(overall_points, overall_points[1:]):
        delta = round(b["value"] - a["value"], 2)
        overall_deltas.append({
            "from_period": a["period_label"],
            "to_period": b["period_label"],
            "delta": delta,
            "direction": _direction(delta),
        })

    if len(parsed_records) < 2:
        warnings.append("fewer than 2 records: trend fields are present but empty -- at least 2 periods are needed to compute a trend")

    result = {
        "student_name": student_name,
        "periods": parsed_records,
        "subject_trends": subject_trends,
        "overall_trend": {
            "points": overall_points,
            "consecutive_deltas": overall_deltas,
            "overall_delta_first_to_last": round(overall_points[-1]["value"] - overall_points[0]["value"], 2) if len(overall_points) >= 2 else None,
        },
    }
    return [], warnings, result


def to_markdown(result: dict) -> str:
    periods = result["periods"]
    subjects = sorted({s for p in periods for s in p["subject_scores"]})
    lines = [
        f"# Bao cao tien do hoc tap -- {result['student_name']}",
        "",
        "| Ky | " + " | ".join(subjects) + " | Diem trung binh chung |",
        "| --- | " + " | ".join(["---"] * len(subjects)) + " | --- |",
    ]
    for p in periods:
        cells = " | ".join(str(p["subject_scores"].get(s, "-")) for s in subjects)
        label = f"{p['overall_value']} ({p['overall_source']})"
        lines.append(f"| {p['period_label']} | {cells} | {label} |")

    lines.extend(["", "## Xu huong tong the (giua cac ky lien tiep)", ""])
    for d in result["overall_trend"]["consecutive_deltas"]:
        arrow = {"up": "^", "down": "v", "flat": "="}[d["direction"]]
        lines.append(f"- {d['from_period']} -> {d['to_period']}: {d['delta']:+.2f} ({arrow} {d['direction']})")

    lines.extend(["", "## Xu huong theo mon", ""])
    for subject, trend in result["subject_trends"].items():
        lines.append(f"### {subject}")
        for d in trend["consecutive_deltas"]:
            arrow = {"up": "^", "down": "v", "flat": "="}[d["direction"]]
            lines.append(f"- {d['from_period']} -> {d['to_period']}: {d['delta']:+.2f} ({arrow} {d['direction']})")
        if not trend["consecutive_deltas"]:
            lines.append("- (chua du du lieu de tinh xu huong)")
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("records", type=Path, help="Path to a progress-records JSON file (see assets/progress_records_template.json)")
    parser.add_argument("--render", type=Path, default=None, help="If validation succeeds, also render a Markdown summary to this path")
    parser.add_argument("--out", type=Path, default=None, help="Also write the full JSON result to this path")
    parser.add_argument("--force", action="store_true", help="Overwrite --render/--out targets if they already exist")
    args = parser.parse_args()

    try:
        data = json.loads(args.records.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings, result = validate_and_compute(data)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    assert result is not None
    print(f"VALID: {len(result['periods'])} period(s) for {result['student_name']}.")

    if args.out:
        if args.out.exists() and not args.force:
            print(f"REFUSED: {args.out} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK: JSON result written to {args.out}")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(result), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    if not args.out and not args.render:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
