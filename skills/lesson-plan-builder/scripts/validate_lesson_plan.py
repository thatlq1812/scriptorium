#!/usr/bin/env python3
"""Validate a K-12 Vietnamese lesson plan (KHBD) JSON record against the
structural requirements of Phu luc IV, Cong van 5512/BGDDT-GDTrH (the
mandatory national lesson-plan format), cross-referenced with the
competency/quality framework in Thong tu 32/2018 (pham chat + nang luc) and
the level-specific assessment rules in Thong tu 27/2020 (tieu hoc: remarks
only, no scores) / Thong tu 22/2021 (THCS/THPT: scores allowed). Stdlib
only, local, deterministic -- no AI/network of any kind.

This checks STRUCTURE, fixed vocabulary, and cross-references -- it does
not judge whether the pedagogy itself is good; that stays the teacher's
call. Errors block (exit 1); warnings are quality signals worth acting on
but don't block (exit 0 with warnings printed).

Usage:
    python validate_lesson_plan.py plan.json [--render plan.md]
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

REQUIRED_ACTIVITY_NAMES = ["Khởi động", "Hình thành kiến thức mới", "Luyện tập", "Vận dụng"]
REQUIRED_STEPS = ["chuyen_giao", "thuc_hien", "bao_cao", "ket_luan"]

FIXED_PHAM_CHAT = {"Yêu nước", "Nhân ái", "Chăm chỉ", "Trung thực", "Trách nhiệm"}
FIXED_NANG_LUC_CHUNG = {"Tự chủ và tự học", "Giao tiếp và hợp tác", "Giải quyết vấn đề và sáng tạo"}
KNOWN_NANG_LUC_DAC_THU = {"Ngôn ngữ", "Tính toán", "Khoa học", "Công nghệ", "Tin học", "Thẩm mỹ", "Thể chất"}

SCORE_LANGUAGE_RE = re.compile(r"cho điểm|chấm điểm|điểm số", re.IGNORECASE)


class LessonPlanError(Exception):
    pass


def infer_cap(khoi_lop: int) -> str:
    if 1 <= khoi_lop <= 5:
        return "TH"
    if 6 <= khoi_lop <= 9:
        return "THCS"
    if 10 <= khoi_lop <= 12:
        return "THPT"
    raise LessonPlanError(f"khoi_lop must be 1-12, got {khoi_lop}")


def validate(plan: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("mon_hoc", "khoi_lop", "ten_bai", "so_tiet", "thoi_luong_phut", "muc_tieu", "hoat_dong", "danh_gia"):
        if field not in plan:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, warnings

    khoi_lop = plan["khoi_lop"]
    if not isinstance(khoi_lop, int):
        errors.append(f"khoi_lop must be an integer, got {khoi_lop!r}")
        return errors, warnings
    try:
        cap = infer_cap(khoi_lop)
    except LessonPlanError as exc:
        errors.append(str(exc))
        return errors, warnings

    mt = plan["muc_tieu"]
    if not isinstance(mt, dict):
        errors.append("muc_tieu must be an object")
        return errors, warnings
    if not mt.get("kien_thuc"):
        errors.append("muc_tieu.kien_thuc is required")

    nang_luc_chung = set(mt.get("nang_luc_chung", []))
    if not nang_luc_chung:
        errors.append("muc_tieu.nang_luc_chung must have at least 1 value")
    invalid_nlc = nang_luc_chung - FIXED_NANG_LUC_CHUNG
    if invalid_nlc:
        errors.append(f"muc_tieu.nang_luc_chung has values outside the official set of 3 (TT32/2018): {sorted(invalid_nlc)}")

    nang_luc_dac_thu = mt.get("nang_luc_dac_thu", [])
    if not nang_luc_dac_thu:
        errors.append("muc_tieu.nang_luc_dac_thu must have at least 1 value")
    for nl in nang_luc_dac_thu:
        if nl not in KNOWN_NANG_LUC_DAC_THU:
            warnings.append(f"nang_luc_dac_thu {nl!r} is not in the CT GDPT 2018 reference list {sorted(KNOWN_NANG_LUC_DAC_THU)} -- verify it's a real subject-specific competency, not a typo")

    pham_chat = set(mt.get("pham_chat", []))
    if not pham_chat:
        errors.append("muc_tieu.pham_chat must have at least 1 value")
    invalid_pc = pham_chat - FIXED_PHAM_CHAT
    if invalid_pc:
        errors.append(f"muc_tieu.pham_chat has values outside the official 5 (CT GDPT 2018): {sorted(invalid_pc)} -- allowed: {sorted(FIXED_PHAM_CHAT)}")

    hoat_dong = plan["hoat_dong"]
    if not isinstance(hoat_dong, list) or len(hoat_dong) != 4:
        errors.append(f"hoat_dong must have exactly 4 activities (Khoi dong / Hinh thanh KT / Luyen tap / Van dung), got {len(hoat_dong) if isinstance(hoat_dong, list) else type(hoat_dong).__name__}")
        hoat_dong = []

    declared_names: list[str] = []
    activity_texts: list[str] = []
    total_activity_minutes = 0
    has_all_minutes = True

    for i, activity in enumerate(hoat_dong):
        if not isinstance(activity, dict):
            errors.append(f"hoat_dong[{i}] must be an object")
            continue
        name = activity.get("ten", "")
        declared_names.append(name)
        expected_name = REQUIRED_ACTIVITY_NAMES[i] if i < len(REQUIRED_ACTIVITY_NAMES) else None
        if expected_name and name != expected_name:
            errors.append(f"hoat_dong[{i}].ten must be {expected_name!r} (fixed order, cannot reorder/rename/merge), got {name!r}")

        for field in ("muc_tieu", "noi_dung", "san_pham"):
            if not activity.get(field):
                errors.append(f"hoat_dong[{i}] ({name}): {field} is required")

        activity_texts.append(" ".join(str(activity.get(f, "")) for f in ("muc_tieu", "noi_dung", "san_pham")))

        steps = activity.get("to_chuc_thuc_hien", {})
        if not isinstance(steps, dict):
            errors.append(f"hoat_dong[{i}] ({name}): to_chuc_thuc_hien must be an object")
        else:
            for step in REQUIRED_STEPS:
                if not steps.get(step):
                    errors.append(f"hoat_dong[{i}] ({name}): to_chuc_thuc_hien.{step} is required (the 4 CV5512 steps: chuyen_giao -> thuc_hien -> bao_cao -> ket_luan)")

        minutes = activity.get("thoi_luong_phut")
        if isinstance(minutes, int):
            total_activity_minutes += minutes
        else:
            has_all_minutes = False

    if len(set(declared_names)) != len(declared_names):
        errors.append("hoat_dong activity names must be distinct (no duplicate activity)")

    # Cross-check: every declared pham_chat/nang_luc must be named in at
    # least one activity's own muc_tieu text -- the "not a fill-in-the-form"
    # quality signal from the CV5512 methodology.
    declared_competencies = pham_chat | nang_luc_chung | set(nang_luc_dac_thu)
    combined_activity_text = " ".join(str(a.get("muc_tieu", "")) for a in hoat_dong if isinstance(a, dict))
    for comp in sorted(declared_competencies):
        if comp not in combined_activity_text:
            warnings.append(f"{comp!r} is declared in muc_tieu but not named in any activity's own muc_tieu -- CV5512 methodology treats this as filled-in-the-form quality, not real pedagogical mapping")

    # Level-specific assessment language check.
    danh_gia = str(plan.get("danh_gia", ""))
    if cap == "TH" and SCORE_LANGUAGE_RE.search(danh_gia):
        errors.append("danh_gia contains scoring language ('cho điểm'/'chấm điểm'/'điểm số') but khoi_lop implies cap Tiểu học (TT27/2020: nhận xét only, no scores in a regular lesson)")

    # Time-allocation check (+/-5%, per the SKILL.md this was elicited from).
    total_minutes = plan.get("thoi_luong_phut")
    if has_all_minutes and isinstance(total_minutes, int) and total_minutes > 0 and hoat_dong:
        deviation = abs(total_activity_minutes - total_minutes) / total_minutes
        if deviation > 0.05:
            warnings.append(f"sum of activity thoi_luong_phut ({total_activity_minutes}) deviates from thoi_luong_phut ({total_minutes}) by {deviation:.0%}, more than the 5% tolerance")

    return errors, warnings


def to_markdown(plan: dict, cap: str) -> str:
    mt = plan["muc_tieu"]
    lines = [
        f"# Kế hoạch bài dạy: {plan['ten_bai']}",
        "",
        f"**Môn học**: {plan['mon_hoc']} | **Khối**: {plan['khoi_lop']} ({cap}) | **Số tiết**: {plan['so_tiet']} | **Thời lượng**: {plan['thoi_luong_phut']} phút",
        "",
        "## Mục tiêu",
        "",
        f"- **Kiến thức**: {mt.get('kien_thuc', '')}",
        f"- **Năng lực chung**: {', '.join(mt.get('nang_luc_chung', []))}",
        f"- **Năng lực đặc thù**: {', '.join(mt.get('nang_luc_dac_thu', []))}",
        f"- **Phẩm chất**: {', '.join(mt.get('pham_chat', []))}",
        "",
        "## Thiết bị dạy học và học liệu",
        "",
    ]
    for item in plan.get("thiet_bi", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Tiến trình dạy học")
    for i, activity in enumerate(plan.get("hoat_dong", []), start=1):
        if not isinstance(activity, dict):
            continue
        steps = activity.get("to_chuc_thuc_hien", {})
        lines.extend([
            "",
            f"### Hoạt động {i} — {activity.get('ten', '')} ({activity.get('thoi_luong_phut', '?')} phút)",
            "",
            f"a) **Mục tiêu**: {activity.get('muc_tieu', '')}",
            f"b) **Nội dung**: {activity.get('noi_dung', '')}",
            f"c) **Sản phẩm**: {activity.get('san_pham', '')}",
            "d) **Tổ chức thực hiện**:",
            f"   1. Chuyển giao nhiệm vụ: {steps.get('chuyen_giao', '')}",
            f"   2. Thực hiện nhiệm vụ: {steps.get('thuc_hien', '')}",
            f"   3. Báo cáo, thảo luận: {steps.get('bao_cao', '')}",
            f"   4. Kết luận, nhận định: {steps.get('ket_luan', '')}",
        ])
    lines.extend(["", "## Đánh giá", "", str(plan.get("danh_gia", ""))])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", type=Path, help="Path to a lesson-plan JSON file (see assets/lesson_plan_template.json)")
    parser.add_argument("--render", type=Path, default=None, help="If validation passes with no errors, also render a Markdown KHBD to this path")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(plan, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = validate(plan)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: structurally complete per Phụ lục IV CV 5512. This confirms structure only, not pedagogical quality.")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        cap = infer_cap(plan["khoi_lop"])
        args.render.write_text(to_markdown(plan, cap), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
