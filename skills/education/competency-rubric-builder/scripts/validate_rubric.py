#!/usr/bin/env python3
"""Validate a competency/product/activity assessment rubric (rubric danh gia
nang luc / san pham / hoat dong) JSON record: a criteria x levels table where
every (criterion, level) cell must carry a non-empty, observable-behavior
description, criterion weights must sum exactly to the declared total scale,
and level descriptions within the same criterion should not be duplicated
verbatim across levels (a cheap, mechanical proxy for a lazy/copy-pasted
rubric). Stdlib only, local, deterministic -- no AI/network of any kind.

This checks STRUCTURE, arithmetic, and literal duplication -- it does not
judge whether the described behaviors are pedagogically appropriate for the
subject/grade; that stays the teacher's call. Errors block (exit 1);
warnings are quality signals worth acting on but don't block (exit 0 with
warnings printed).

Usage:
    python validate_rubric.py rubric.json [--render rubric.md] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

ALLOWED_MUC_COUNTS = (3, 4)


class RubricError(Exception):
    pass


def validate(rubric: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("doi_tuong_danh_gia", "muc", "thang_diem_tong", "tieu_chi"):
        if field not in rubric:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, warnings

    muc = rubric["muc"]
    if not isinstance(muc, list) or not all(isinstance(m, str) and m for m in muc):
        errors.append("muc must be a list of non-empty level names")
        return errors, warnings
    if len(muc) not in ALLOWED_MUC_COUNTS:
        errors.append(f"muc must have 3 or 4 levels (ordered high -> low quality), got {len(muc)}")
        return errors, warnings
    if len(set(muc)) != len(muc):
        errors.append(f"muc level names must be distinct, got {muc}")

    thang_diem_tong = rubric["thang_diem_tong"]
    if not isinstance(thang_diem_tong, (int, float)) or isinstance(thang_diem_tong, bool):
        errors.append(f"thang_diem_tong must be a number, got {thang_diem_tong!r}")
        return errors, warnings

    tieu_chi = rubric["tieu_chi"]
    if not isinstance(tieu_chi, list) or not tieu_chi:
        errors.append("tieu_chi must be a non-empty list of criteria")
        return errors, warnings

    declared_names: list[str] = []
    weight_sum: float = 0
    has_all_weights = True

    for i, criterion in enumerate(tieu_chi):
        if not isinstance(criterion, dict):
            errors.append(f"tieu_chi[{i}] must be an object")
            continue

        ten = criterion.get("ten", "")
        if not ten:
            errors.append(f"tieu_chi[{i}]: ten (criterion name) is required")
            ten = f"<tieu_chi[{i}]>"
        declared_names.append(ten)

        trong_so = criterion.get("trong_so")
        if isinstance(trong_so, (int, float)) and not isinstance(trong_so, bool):
            weight_sum += trong_so
        else:
            has_all_weights = False
            errors.append(f"tieu_chi[{i}] ({ten}): trong_so must be a number, got {trong_so!r}")

        mo_ta = criterion.get("mo_ta")
        if not isinstance(mo_ta, dict):
            errors.append(f"tieu_chi[{i}] ({ten}): mo_ta must be an object mapping level name -> description")
            continue

        seen_texts: dict[str, list[str]] = {}
        for level in muc:
            desc = mo_ta.get(level)
            if not isinstance(desc, str) or not desc.strip():
                errors.append(f"tieu_chi[{i}] ({ten}): missing or empty mo_ta for level {level!r}")
                continue
            seen_texts.setdefault(desc.strip(), []).append(level)

        extra_levels = set(mo_ta.keys()) - set(muc)
        if extra_levels:
            warnings.append(f"tieu_chi[{i}] ({ten}): mo_ta has level(s) not in muc: {sorted(extra_levels)} -- ignored")

        for text, levels_with_text in seen_texts.items():
            if len(levels_with_text) > 1:
                warnings.append(
                    f"tieu_chi[{i}] ({ten}): identical description text reused across levels {levels_with_text} "
                    f"-- descriptions should be distinct per level, not copy-pasted"
                )

    if len(set(declared_names)) != len(declared_names):
        errors.append("tieu_chi criterion names (ten) must be distinct (no duplicate criterion)")

    if has_all_weights:
        if weight_sum != thang_diem_tong:
            diff = thang_diem_tong - weight_sum
            direction = "short by" if diff > 0 else "over by"
            errors.append(
                f"sum(tieu_chi[].trong_so) = {weight_sum} does not equal thang_diem_tong = {thang_diem_tong} "
                f"({direction} {abs(diff)})"
            )

    return errors, warnings


def to_markdown(rubric: dict) -> str:
    muc = rubric["muc"]
    tieu_chi = rubric["tieu_chi"]
    doi_tuong = rubric["doi_tuong_danh_gia"]
    khoi_lop = rubric.get("khoi_lop", "")
    thang_diem_tong = rubric["thang_diem_tong"]

    lines = [f"# Rubric đánh giá: {doi_tuong}", ""]
    if khoi_lop:
        lines.append(f"**Khối lớp**: {khoi_lop}")
        lines.append("")
    lines.append(f"**Thang điểm tổng**: {thang_diem_tong}")
    lines.append("")

    header = ["Tiêu chí"] + list(muc) + ["Trọng số"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")

    weight_sum: float = 0
    for criterion in tieu_chi:
        ten = criterion.get("ten", "")
        mo_ta = criterion.get("mo_ta", {})
        trong_so = criterion.get("trong_so", 0)
        weight_sum += trong_so
        row = [ten] + [str(mo_ta.get(level, "")).replace("|", "\\|").replace("\n", " ") for level in muc] + [str(trong_so)]
        lines.append("| " + " | ".join(row) + " |")

    total_row = ["**Tổng**"] + [""] * len(muc) + [f"**{weight_sum}**"]
    lines.append("| " + " | ".join(total_row) + " |")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rubric", type=Path, help="Path to a rubric JSON file (see assets/rubric_template.json)")
    parser.add_argument("--render", type=Path, default=None, help="If validation passes with no errors, also render a Markdown rubric table to this path")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        rubric = json.loads(args.rubric.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(rubric, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = validate(rubric)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: structurally complete -- every cell filled, weights sum matches thang_diem_tong. This confirms structure/arithmetic only, not pedagogical quality.")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(rubric), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
