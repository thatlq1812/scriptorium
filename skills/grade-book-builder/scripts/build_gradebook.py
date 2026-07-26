#!/usr/bin/env python3
"""Build a class-wide gradebook (so tong hop diem) from a filled gradebook
JSON record: per-student weighted term average (TBM) across declared
assessment categories, a classification against user-declared bands, and
class-wide statistics. Stdlib only, local, deterministic -- no AI/network
of any kind, no invented official weight percentages or classification
thresholds (those are required inputs, see assets/gradebook_template.json).

This aggregates ALREADY-SCORED assessment results into a term-level
gradebook. It does not grade any individual assessment (that is a
different skill's job) and does not assert TT22/2021 weights/bands as
verified official fact -- it computes strictly against whatever
category_weights / classification_bands the caller declares.

Usage:
    python build_gradebook.py <gradebook.json> [--render summary.md] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

SCORE_MIN = 0.0
SCORE_MAX = 10.0
WEIGHT_SUM_TOLERANCE = 1e-6


class GradebookError(Exception):
    pass


def _round(value: float, digits: int) -> float:
    return round(value, digits)


def validate_and_compute(gb: dict) -> tuple[list[str], dict | None]:
    """Returns (errors, result). result is None if errors is non-empty."""
    errors: list[str] = []

    for field in ("class_name", "students", "category_weights", "classification_bands"):
        if field not in gb:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, None

    class_name = gb["class_name"]
    if not isinstance(class_name, str) or not class_name.strip():
        errors.append("class_name must be a non-empty string")

    category_weights = gb["category_weights"]
    if not isinstance(category_weights, dict) or not category_weights:
        errors.append("category_weights must be a non-empty object")
        return errors, None
    for cat, w in category_weights.items():
        if not isinstance(w, (int, float)) or isinstance(w, bool) or w <= 0:
            errors.append(f"category_weights[{cat!r}] must be a positive number, got {w!r}")
    if errors:
        return errors, None

    weight_total_declared = gb.get("weight_total", 1.0)
    if not isinstance(weight_total_declared, (int, float)) or isinstance(weight_total_declared, bool) or weight_total_declared <= 0:
        errors.append(f"weight_total must be a positive number, got {weight_total_declared!r}")
        return errors, None

    actual_weight_sum = sum(category_weights.values())
    if abs(actual_weight_sum - weight_total_declared) > WEIGHT_SUM_TOLERANCE:
        errors.append(
            f"category_weights values sum to {actual_weight_sum!r}, "
            f"but weight_total is declared as {weight_total_declared!r} -- these must match "
            f"(either fix category_weights, or set weight_total to the intended total, e.g. 1.0)"
        )
        return errors, None

    round_digits = gb.get("round_digits", 1)
    if not isinstance(round_digits, int) or isinstance(round_digits, bool) or round_digits < 0:
        errors.append(f"round_digits must be a non-negative integer, got {round_digits!r}")
        return errors, None

    bands = gb["classification_bands"]
    if not isinstance(bands, list) or not bands:
        errors.append("classification_bands must be a non-empty list")
        return errors, None
    parsed_bands: list[tuple[str, float]] = []
    for i, band in enumerate(bands):
        if not isinstance(band, dict) or "label" not in band or "min_score" not in band:
            errors.append(f"classification_bands[{i}] must be an object with 'label' and 'min_score'")
            continue
        label = band["label"]
        min_score = band["min_score"]
        if not isinstance(label, str) or not label.strip():
            errors.append(f"classification_bands[{i}].label must be a non-empty string")
        if not isinstance(min_score, (int, float)) or isinstance(min_score, bool):
            errors.append(f"classification_bands[{i}].min_score must be a number, got {min_score!r}")
            continue
        parsed_bands.append((label, float(min_score)))
    if errors:
        return errors, None

    for i in range(1, len(parsed_bands)):
        if not (parsed_bands[i - 1][1] > parsed_bands[i][1]):
            errors.append(
                f"classification_bands must be strictly descending by min_score -- "
                f"band {i - 1} ({parsed_bands[i-1][0]!r}: {parsed_bands[i-1][1]}) is not > "
                f"band {i} ({parsed_bands[i][0]!r}: {parsed_bands[i][1]})"
            )
            break
    if errors:
        return errors, None

    students = gb["students"]
    if not isinstance(students, list) or not students:
        errors.append("students must be a non-empty list")
        return errors, None

    declared_categories = set(category_weights.keys())
    used_categories: set[str] = set()
    seen_ids: list[str] = []
    student_rows: list[dict] = []

    for i, student in enumerate(students):
        if not isinstance(student, dict) or "id" not in student or "name" not in student or "scores" not in student:
            errors.append(f"students[{i}] must be an object with 'id', 'name', 'scores'")
            continue
        sid = student["id"]
        name = student["name"]
        scores = student["scores"]
        if not isinstance(sid, str) or not sid.strip():
            errors.append(f"students[{i}].id must be a non-empty string")
            continue
        if not isinstance(name, str) or not name.strip():
            errors.append(f"students[{i}] ({sid}): name must be a non-empty string")
        if not isinstance(scores, dict):
            errors.append(f"students[{i}] ({sid}): scores must be an object")
            continue
        seen_ids.append(sid)

        unknown_cats = set(scores.keys()) - declared_categories
        if unknown_cats:
            errors.append(
                f"students[{i}] ({sid}): scores use categor{'y' if len(unknown_cats)==1 else 'ies'} "
                f"{sorted(unknown_cats)} not declared in category_weights {sorted(declared_categories)}"
            )
            continue

        missing_cats = declared_categories - set(scores.keys())
        if missing_cats:
            errors.append(
                f"students[{i}] ({sid}): missing score(s) for declared categor{'y' if len(missing_cats)==1 else 'ies'} "
                f"{sorted(missing_cats)} -- every declared category needs at least one score per student "
                f"(the weighted average cannot be computed with a category left out)"
            )
            continue

        category_averages: dict[str, float] = {}
        row_ok = True
        for cat, raw_scores in scores.items():
            if not isinstance(raw_scores, list) or not raw_scores:
                errors.append(f"students[{i}] ({sid}): scores[{cat!r}] must be a non-empty list of numbers")
                row_ok = False
                continue
            numeric_scores: list[float] = []
            for s in raw_scores:
                if not isinstance(s, (int, float)) or isinstance(s, bool):
                    errors.append(f"students[{i}] ({sid}): scores[{cat!r}] contains a non-numeric value {s!r}")
                    row_ok = False
                    continue
                if not (SCORE_MIN <= s <= SCORE_MAX):
                    errors.append(
                        f"students[{i}] ({sid}): scores[{cat!r}] value {s!r} is outside the "
                        f"{SCORE_MIN}-{SCORE_MAX} scale"
                    )
                    row_ok = False
                    continue
                numeric_scores.append(float(s))
            if numeric_scores:
                category_averages[cat] = sum(numeric_scores) / len(numeric_scores)
                used_categories.add(cat)

        if not row_ok:
            continue

        weighted_sum = sum(category_averages[cat] * category_weights[cat] for cat in category_averages)
        tbm = _round(weighted_sum / actual_weight_sum, round_digits)

        student_rows.append(
            {
                "id": sid,
                "name": name,
                "category_averages": {cat: _round(v, round_digits) for cat, v in category_averages.items()},
                "tbm": tbm,
            }
        )

    if len(set(seen_ids)) != len(seen_ids):
        dupes = sorted({sid for sid in seen_ids if seen_ids.count(sid) > 1})
        errors.append(f"students have duplicate id(s): {dupes}")

    unused_categories = declared_categories - used_categories
    if unused_categories:
        errors.append(
            f"category_weights declares categor{'y' if len(unused_categories)==1 else 'ies'} "
            f"{sorted(unused_categories)} that no student ever uses -- remove it from category_weights "
            f"or add at least one student score for it"
        )

    if errors:
        return errors, None

    # Classify each student against the strictly-descending bands (first
    # band whose min_score the TBM meets or exceeds).
    for row in student_rows:
        tbm = row["tbm"]
        label = None
        for band_label, min_score in parsed_bands:
            if tbm >= min_score:
                label = band_label
                break
        if label is None:
            label = f"<below lowest band ({parsed_bands[-1][1]})>"
        row["classification"] = label

    tbm_values = [row["tbm"] for row in student_rows]
    class_stats = {
        "count": len(student_rows),
        "average": _round(sum(tbm_values) / len(tbm_values), round_digits),
        "max": max(tbm_values),
        "min": min(tbm_values),
    }

    by_label: dict[str, list[float]] = {}
    for row in student_rows:
        by_label.setdefault(row["classification"], []).append(row["tbm"])
    classification_stats = []
    for label, _min_score in parsed_bands:
        values = by_label.get(label, [])
        classification_stats.append(
            {
                "label": label,
                "count": len(values),
                "average": _round(sum(values) / len(values), round_digits) if values else None,
                "max": max(values) if values else None,
                "min": min(values) if values else None,
            }
        )

    result = {
        "class_name": class_name,
        "category_weights": category_weights,
        "weight_total": actual_weight_sum,
        "round_digits": round_digits,
        "students": student_rows,
        "class_stats": class_stats,
        "classification_stats": classification_stats,
    }
    return [], result


def to_markdown(result: dict) -> str:
    categories = list(result["category_weights"].keys())
    lines = [
        f"# Sổ tổng hợp điểm — {result['class_name']}",
        "",
        f"Trọng số: {', '.join(f'{c}={w}' for c, w in result['category_weights'].items())} "
        f"(tổng = {result['weight_total']}, làm tròn {result['round_digits']} chữ số thập phân)",
        "",
        "| STT | Họ và tên | " + " | ".join(categories) + " | TBM | Xếp loại |",
        "| --- | --- | " + " | ".join(["---"] * len(categories)) + " | --- | --- |",
    ]
    for i, row in enumerate(result["students"], start=1):
        cat_cells = " | ".join(str(row["category_averages"].get(c, "")) for c in categories)
        lines.append(f"| {i} | {row['name']} | {cat_cells} | {row['tbm']} | {row['classification']} |")

    stats = result["class_stats"]
    lines.extend(
        [
            "",
            "## Thống kê lớp",
            "",
            f"- Sĩ số: {stats['count']}",
            f"- TBM trung bình lớp: {stats['average']}",
            f"- TBM cao nhất: {stats['max']} | TBM thấp nhất: {stats['min']}",
            "",
            "| Xếp loại | Số lượng | TBM trung bình | TBM cao nhất | TBM thấp nhất |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for cs in result["classification_stats"]:
        lines.append(
            f"| {cs['label']} | {cs['count']} | {cs['average'] if cs['average'] is not None else '-'} | "
            f"{cs['max'] if cs['max'] is not None else '-'} | {cs['min'] if cs['min'] is not None else '-'} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("gradebook", type=Path, help="Path to a filled gradebook JSON file (see assets/gradebook_template.json)")
    parser.add_argument("--render", type=Path, default=None, help="If computation succeeds, also render a Markdown summary table to this path")
    parser.add_argument("--out", type=Path, default=None, help="Also write the full JSON result to this path")
    parser.add_argument("--force", action="store_true", help="Overwrite --render/--out targets if they already exist")
    args = parser.parse_args()

    try:
        gb = json.loads(args.gradebook.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(gb, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, result = validate_and_compute(gb)

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    assert result is not None
    print(f"VALID: {result['class_stats']['count']} học sinh, TBM lớp trung bình = {result['class_stats']['average']}")

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
