#!/usr/bin/env python3
"""Build a balanced exam matrix (ma tran de) for a Vietnamese K-12 exam.

Given a list of topics (rows), a total question count, a total point value,
and a 4-level cognitive-level ratio (Nhan biet / Thong hieu / Van dung / Van
dung cao -- default 40/30/20/10), deterministically compute how many
questions and how many points go in each (topic x level) cell, using the
largest-remainder (Hamilton apportionment) method so the allocated counts
and points always sum EXACTLY to the requested totals -- no off-by-one
drift from naive rounding.

This script does not generate question content. It produces a "plan" (the
balanced matrix) that a human or the calling agent then fills with actual
question text via exam.json (see validate_exam.py + assets/exam_template.json).

Stdlib only, local, deterministic -- no AI/network of any kind.

Usage:
    python build_exam_matrix.py <input.json> -o plan.json [--render matrix.md] [--profile <name>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

LEVELS: tuple[tuple[str, str], ...] = (
    ("nhan_biet", "Nhận biết"),
    ("thong_hieu", "Thông hiểu"),
    ("van_dung", "Vận dụng"),
    ("van_dung_cao", "Vận dụng cao"),
)
LEVEL_KEYS: tuple[str, ...] = tuple(k for k, _ in LEVELS)

DEFAULT_RATIO: dict[str, float] = {
    "nhan_biet": 40.0,
    "thong_hieu": 30.0,
    "van_dung": 20.0,
    "van_dung_cao": 10.0,
}

# A named ratio-set is a *label*, not an official regulation lookup -- see
# SKILL.md "Known limitations". "qd4068_thpt" mirrors the same 40/30/20/10
# default EduStation's tn_thpt_review skill used for the QD 4068 THPT
# graduation-exam profile (per the 18/10/2024 sample-exam Bloom ratio for
# the natural-science group); it is NOT a per-subject official ratio table
# and must not be presented as one.
PROFILES: dict[str, dict[str, float]] = {
    "default": dict(DEFAULT_RATIO),
    "qd4068_thpt": dict(DEFAULT_RATIO),
}


class MatrixError(Exception):
    pass


def largest_remainder_int(total: int, weights: list[float]) -> list[int]:
    """Apportion an integer `total` across `weights` (Hamilton / largest-
    remainder method). Always returns a list of non-negative ints summing to
    exactly `total`, proportional to weights. Ties in the fractional
    remainder go to the earliest index (deterministic)."""
    n = len(weights)
    if n == 0:
        if total != 0:
            raise MatrixError("cannot apportion a non-zero total across zero items")
        return []
    if total < 0:
        raise MatrixError("cannot apportion a negative total")
    if total == 0:
        return [0] * n
    sum_w = sum(weights)
    if sum_w <= 0:
        # No usable weights -- fall back to equal weight so the total is
        # still distributed (never silently dropped).
        weights = [1.0] * n
        sum_w = float(n)
    shares = [total * w / sum_w for w in weights]
    floors = [int(s) for s in shares]  # truncation toward zero; weights are >= 0
    remainder = total - sum(floors)
    order = sorted(range(n), key=lambda i: (-(shares[i] - floors[i]), i))
    for i in range(remainder):
        floors[order[i]] += 1
    return floors


def largest_remainder_cents(total: float, weights: list[float]) -> list[float]:
    """Same idea as largest_remainder_int but for a monetary/point-style
    quantity: apportions in integer cents (total * 100, rounded) then
    divides back down, so the returned floats sum to exactly `total`
    (within floating-point display, i.e. round-tripping the cent integers)."""
    total_cents = round(total * 100)
    cents = largest_remainder_int(total_cents, weights)
    return [c / 100 for c in cents]


def _norm_ratio(raw: object, profile: str | None) -> dict[str, float]:
    """Coerce a ratio dict to four percentages summing to 100. Missing/
    invalid falls back to the selected profile's default (itself falling
    back to 40/30/20/10). A ratio that does not sum to 100 is rescaled
    proportionally, never silently dropped."""
    base = PROFILES.get(profile or "default")
    if base is None:
        raise MatrixError(
            f"unknown profile {profile!r} -- known profiles: {sorted(PROFILES)}"
        )
    ratio = dict(base)
    if isinstance(raw, dict):
        for key in LEVEL_KEYS:
            val = raw.get(key)
            if isinstance(val, (int, float)) and not isinstance(val, bool) and val >= 0:
                ratio[key] = float(val)
    total = sum(ratio.values())
    if total <= 0:
        raise MatrixError("level_ratio values sum to 0 -- cannot allocate")
    rescaled_cents = largest_remainder_int(10000, [ratio[k] for k in LEVEL_KEYS])
    return {k: v / 100 for k, v in zip(LEVEL_KEYS, rescaled_cents)}


def _load_input(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MatrixError(f"input unreadable/malformed: {exc}") from exc
    if not isinstance(data, dict):
        raise MatrixError("input top-level JSON must be an object")
    return data


def build(input_data: dict, profile: str | None) -> dict:
    raw_topics = input_data.get("topics")
    if not isinstance(raw_topics, list) or not raw_topics:
        raise MatrixError("'topics' must be a non-empty list")
    topics: list[str] = []
    topic_weights: list[float] = []
    for i, t in enumerate(raw_topics):
        if isinstance(t, str):
            name, weight = t.strip(), 1.0
        elif isinstance(t, dict):
            name = str(t.get("name", "")).strip()
            weight = t.get("weight", 1)
            if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight <= 0:
                weight = 1.0
            weight = float(weight)
        else:
            raise MatrixError(f"topics[{i}] must be a string or an object with 'name'")
        if not name:
            raise MatrixError(f"topics[{i}] has an empty name")
        topics.append(name)
        topic_weights.append(weight)
    if len(set(topics)) != len(topics):
        raise MatrixError("topic names must be distinct")

    total_questions = input_data.get("total_questions")
    if not isinstance(total_questions, int) or isinstance(total_questions, bool) or total_questions <= 0:
        raise MatrixError("'total_questions' must be a positive integer")
    if total_questions < len(topics):
        # Not an error -- some topic x level cells will legitimately be 0 --
        # but worth surfacing since it changes matrix shape drastically.
        pass

    total_points = input_data.get("total_points", 10)
    if not isinstance(total_points, (int, float)) or isinstance(total_points, bool) or total_points <= 0:
        raise MatrixError("'total_points' must be a positive number")
    total_points = float(total_points)

    ratio = _norm_ratio(input_data.get("level_ratio"), profile)

    level_ratio_pct = {k: ratio[k] for k in LEVEL_KEYS}
    level_counts_list = largest_remainder_int(total_questions, [ratio[k] for k in LEVEL_KEYS])
    level_counts = dict(zip(LEVEL_KEYS, level_counts_list))

    # Points are allocated by the SAME ratio, but a level with zero allocated
    # questions must receive zero points -- points can never attach to a
    # question that doesn't exist. Zero that level's weight so its share of
    # total_points is redistributed (largest-remainder) across the levels
    # that actually have questions; the sum still lands exactly on
    # total_points. At least one level is guaranteed to have count > 0 since
    # total_questions >= 1.
    points_weights = [ratio[k] if level_counts[k] > 0 else 0.0 for k in LEVEL_KEYS]
    level_points_list = largest_remainder_cents(total_points, points_weights)
    level_points = dict(zip(LEVEL_KEYS, level_points_list))

    grid_counts: dict[str, dict[str, int]] = {}
    grid_points: dict[str, dict[str, float]] = {}
    for key in LEVEL_KEYS:
        counts = largest_remainder_int(level_counts[key], topic_weights)
        grid_counts[key] = dict(zip(topics, counts))
        # Same zero-weight rule at cell granularity: a (topic x level) cell
        # with zero questions gets zero points; its share is redistributed
        # to cells in the same level/row that do have questions.
        cell_weights = [w if counts[i] > 0 else 0.0 for i, w in enumerate(topic_weights)]
        pts = largest_remainder_cents(level_points[key], cell_weights)
        grid_points[key] = dict(zip(topics, pts))

    plan = {
        "topics": topics,
        "topic_weights": dict(zip(topics, topic_weights)),
        "total_questions": total_questions,
        "total_points": total_points,
        "profile": profile or "default",
        "level_ratio": level_ratio_pct,
        "level_counts": level_counts,
        "level_points": level_points,
        "grid_counts": grid_counts,
        "grid_points": grid_points,
        "note": (
            "This plan is the single source of truth for exam.json. The exam "
            "content must match this allocation exactly (validate_exam.py "
            "enforces it) -- never hand-adjust counts after the fact; edit the "
            "input and re-run build_exam_matrix.py instead."
        ),
    }
    return plan


def _fmt_points(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:g}"


def render_markdown(plan: dict) -> str:
    topics: list[str] = plan["topics"]
    grid_counts = plan["grid_counts"]
    grid_points = plan["grid_points"]
    level_counts = plan["level_counts"]
    level_points = plan["level_points"]

    header = "| Chủ đề / Nội dung | " + " | ".join(vn for _, vn in LEVELS) + " | Tổng |"
    sep = "| " + " | ".join(["---"] * (len(LEVELS) + 2)) + " |"
    lines = [
        "# MA TRẬN ĐỀ",
        "",
        f"- Tổng số câu: {plan['total_questions']} — Tổng điểm: {_fmt_points(plan['total_points'])}",
        f"- Tỉ lệ theo mức độ nhận thức (%): "
        + ", ".join(f"{vn} {_fmt_points(plan['level_ratio'][key])}" for key, vn in LEVELS),
        f"- Profile: {plan['profile']}",
        "",
        header,
        sep,
    ]
    for topic in topics:
        cells = [f"{grid_counts[key][topic]} ({_fmt_points(grid_points[key][topic])}đ)" for key, _ in LEVELS]
        row_total_q = sum(grid_counts[key][topic] for key, _ in LEVELS)
        row_total_p = sum(grid_points[key][topic] for key, _ in LEVELS)
        lines.append(f"| {topic} | " + " | ".join(cells) + f" | {row_total_q} ({_fmt_points(row_total_p)}đ) |")
    total_cau = "| **Tổng số câu** | " + " | ".join(str(level_counts[key]) for key, _ in LEVELS) + f" | {plan['total_questions']} |"
    total_diem = "| **Tổng điểm** | " + " | ".join(_fmt_points(level_points[key]) for key, _ in LEVELS) + f" | {_fmt_points(plan['total_points'])} |"
    lines += [total_cau, total_diem]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="Path to an input JSON file (see assets/exam_matrix_input_template.json)")
    parser.add_argument("-o", "--out", type=Path, default=Path("plan.json"), help="Where to write the balanced plan JSON (default: plan.json)")
    parser.add_argument("--render", type=Path, default=None, help="Also render the matrix to this Markdown path")
    parser.add_argument("--profile", type=str, default=None, help=f"Named ratio-set to use as the default level_ratio when the input doesn't override it. Known: {sorted(PROFILES)}")
    parser.add_argument("--force", action="store_true", help="Overwrite --out/--render if they already exist")
    args = parser.parse_args()

    try:
        input_data = _load_input(args.input)
        plan = build(input_data, args.profile)
    except MatrixError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    if args.out.exists() and not args.force:
        print(f"REFUSED: {args.out} already exists, use --force to overwrite", file=sys.stderr)
        return 2
    args.out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    counts_str = " / ".join(f"{vn} {plan['level_counts'][key]}" for key, vn in LEVELS)
    points_str = " / ".join(f"{vn} {_fmt_points(plan['level_points'][key])}" for key, vn in LEVELS)
    print(f"PLAN: {args.out}")
    print(f"COUNTS: {counts_str} (sum={sum(plan['level_counts'].values())}, expected={plan['total_questions']})")
    print(f"POINTS: {points_str} (sum={sum(plan['level_points'].values()):g}, expected={_fmt_points(plan['total_points'])})")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(render_markdown(plan), encoding="utf-8")
        print(f"MATRIX: {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
