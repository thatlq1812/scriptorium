#!/usr/bin/env python3
"""Validate an exam.json against a plan.json produced by build_exam_matrix.py.

Checks that the actual exam content structurally and numerically matches the
balanced matrix: right number of questions per cognitive level (MCQ + essay
combined), right number per (topic x level) cell, every MCQ has exactly 4
distinct choices and exactly one valid answer, every essay question's
grading guide sums to its own points, and total points sum to the plan's
total. This is a pure structural/numeric conformance check -- it does NOT
judge whether the questions are good, correct, or on-topic; that stays a
human/subject-matter call.

Refuses loudly (nonzero exit) on any mismatch, naming exactly what is off --
never silently accepts a malformed exam.

Stdlib only, local, deterministic -- no AI/network of any kind.

Usage:
    python validate_exam.py <plan.json> <exam.json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

LEVEL_KEYS: tuple[str, ...] = ("nhan_biet", "thong_hieu", "van_dung", "van_dung_cao")
POINT_TOLERANCE = 0.01
ANSWER_LABELS = "ABCDEFGH"  # supports up to 8 choices; MCQs here require exactly 4


def _load_json(path: Path, label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"MALFORMED: {label} unreadable/malformed: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"MALFORMED: {label} top-level JSON must be an object")
    return data


def validate(plan: dict, exam: dict) -> list[str]:
    """Returns a list of error strings (empty = valid)."""
    errors: list[str] = []

    for field in ("topics", "total_questions", "total_points", "level_counts", "grid_counts"):
        if field not in plan:
            errors.append(f"plan.json missing required field: {field}")
    if errors:
        return errors

    topics: list[str] = plan["topics"]
    topic_set = set(topics)

    mcq = exam.get("mcq", [])
    essay = exam.get("essay", [])
    if not isinstance(mcq, list):
        errors.append("exam.mcq must be a list")
        mcq = []
    if not isinstance(essay, list):
        errors.append("exam.essay must be a list")
        essay = []

    level_actual: dict[str, int] = {k: 0 for k in LEVEL_KEYS}
    cell_actual: dict[str, dict[str, int]] = {k: {t: 0 for t in topics} for k in LEVEL_KEYS}
    total_points_actual = 0.0

    def _check_common(q: dict, idx: int, kind: str) -> tuple[str | None, str | None]:
        topic = q.get("topic")
        level = q.get("level")
        points = q.get("points")
        if not isinstance(topic, str) or not topic.strip():
            errors.append(f"{kind}[{idx}]: 'topic' is required")
            topic = None
        elif topic not in topic_set:
            errors.append(f"{kind}[{idx}]: topic {topic!r} is not one of the plan's topics {topics}")
            topic = None
        if level not in LEVEL_KEYS:
            errors.append(f"{kind}[{idx}]: 'level' must be one of {LEVEL_KEYS}, got {level!r}")
            level = None
        if not isinstance(points, (int, float)) or isinstance(points, bool) or points <= 0:
            errors.append(f"{kind}[{idx}]: 'points' must be a positive number, got {points!r}")
            points = None
        return topic, level

    for i, q in enumerate(mcq):
        if not isinstance(q, dict):
            errors.append(f"mcq[{i}] must be an object")
            continue
        topic, level = _check_common(q, i, "mcq")
        choices = q.get("choices")
        answer = q.get("answer")
        if not isinstance(choices, list) or len(choices) != 4:
            errors.append(f"mcq[{i}]: 'choices' must be a list of exactly 4 items, got {len(choices) if isinstance(choices, list) else type(choices).__name__}")
        else:
            texts = [str(c).strip() for c in choices]
            if any(not t for t in texts):
                errors.append(f"mcq[{i}]: 'choices' must not contain empty text")
            if len(set(texts)) != len(texts):
                errors.append(f"mcq[{i}]: 'choices' must be 4 distinct values, found a duplicate")
            valid_labels = ANSWER_LABELS[: len(choices)]
            if not isinstance(answer, str) or answer.strip().upper() not in valid_labels:
                errors.append(f"mcq[{i}]: 'answer' must be exactly one of {list(valid_labels)}, got {answer!r}")

        points = q.get("points")
        if isinstance(points, (int, float)) and not isinstance(points, bool) and points > 0:
            total_points_actual += float(points)
        if topic is not None and level is not None:
            level_actual[level] += 1
            cell_actual[level][topic] += 1

    for i, q in enumerate(essay):
        if not isinstance(q, dict):
            errors.append(f"essay[{i}] must be an object")
            continue
        topic, level = _check_common(q, i, "essay")
        points = q.get("points")
        guide = q.get("grading_guide")
        if not isinstance(guide, list) or not guide:
            errors.append(f"essay[{i}]: 'grading_guide' must be a non-empty list")
        else:
            guide_sum = 0.0
            guide_ok = True
            for j, item in enumerate(guide):
                if not isinstance(item, dict) or not isinstance(item.get("criterion"), str) or not item.get("criterion", "").strip():
                    errors.append(f"essay[{i}].grading_guide[{j}]: 'criterion' is required")
                    guide_ok = False
                item_points = item.get("points") if isinstance(item, dict) else None
                if not isinstance(item_points, (int, float)) or isinstance(item_points, bool) or item_points <= 0:
                    errors.append(f"essay[{i}].grading_guide[{j}]: 'points' must be a positive number, got {item_points!r}")
                    guide_ok = False
                else:
                    guide_sum += float(item_points)
            if guide_ok and isinstance(points, (int, float)) and not isinstance(points, bool) and points > 0:
                if abs(guide_sum - points) > POINT_TOLERANCE:
                    errors.append(f"essay[{i}]: grading_guide sums to {guide_sum:g} but essay points is {points:g} (must match within {POINT_TOLERANCE})")

        if isinstance(points, (int, float)) and not isinstance(points, bool) and points > 0:
            total_points_actual += float(points)
        if topic is not None and level is not None:
            level_actual[level] += 1
            cell_actual[level][topic] += 1

    total_actual = len(mcq) + len(essay)
    if total_actual != plan["total_questions"]:
        errors.append(f"total question count: expected {plan['total_questions']} (from plan.json), got {total_actual}")

    for level in LEVEL_KEYS:
        expected = plan["level_counts"].get(level)
        actual = level_actual[level]
        if expected is not None and actual != expected:
            errors.append(f"level {level!r}: expected {expected} questions, got {actual}")

    for level in LEVEL_KEYS:
        expected_row = plan["grid_counts"].get(level, {})
        for topic in topics:
            expected = expected_row.get(topic, 0)
            actual = cell_actual[level][topic]
            if actual != expected:
                errors.append(f"topic {topic!r} x level {level!r}: expected {expected} questions, got {actual}")

    expected_total_points = plan["total_points"]
    if isinstance(expected_total_points, (int, float)) and abs(total_points_actual - expected_total_points) > POINT_TOLERANCE:
        errors.append(f"total points: expected {expected_total_points:g} (from plan.json), got {total_points_actual:g}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", type=Path, help="Path to plan.json (from build_exam_matrix.py)")
    parser.add_argument("exam", type=Path, help="Path to exam.json (see assets/exam_template.json)")
    args = parser.parse_args()

    plan = _load_json(args.plan, "plan.json")
    exam = _load_json(args.exam, "exam.json")

    errors = validate(plan, exam)

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: exam.json structurally and numerically matches plan.json. This confirms conformance to the matrix only, not question quality or correctness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
