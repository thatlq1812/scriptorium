#!/usr/bin/env python3
"""Generates a valid html-poster-composer layout.json + content.json for a
common Vietnamese social/administrative announcement poster, from
structured, non-technical input -- no zone taxonomy, no x/y/w/h percentage
math required from the caller. Covers 3 real content shapes: a decree/
directive summary (tom tat van ban), a general notice (thong bao), and a
contest/competition result announcement (ket qua cuoc thi). Stdlib only
(json, argparse), local, deterministic -- no AI/network call.

This skill does NOT render pixels itself -- it produces layout.json +
content.json conforming exactly to html-poster-composer's own schema
(layout_schema.py/validate_content.py), which the calling agent then runs
through that skill's compose.py unchanged. Same "generate valid input for
a real render engine" shape as design-system-recommender ->
landing-page-composer.

Exit codes: 0 = generated, 1 = validation issue in the caller's fields,
2 = malformed input/args.

Usage:
    python build_announcement_poster.py <request.json> --out-dir <dir>
    (writes <dir>/layout.json and <dir>/content.json)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

CONTENT_TYPES = ("decree_summary", "announcement", "contest_result")
CANVAS_CHOICES = {"square": "SQUARE", "a4": "A4"}

# Mirrors html-poster-composer's own layout_schema.py MAX_TEXT_COVERAGE_PCT
# (duplicated as a constant, not cross-imported, since that skill lives in
# a different domain folder and this project's convention is a sibling
# skill copies a small constant rather than reaching across a domain
# boundary for one value). Checked here as a SELF-TEST against this
# script's own hardcoded template zone percentages -- found for real
# during this skill's own build/test round: a hand-calculated zone budget
# that forgot to include the "kicker" zone's own area, silently exceeding
# the real limit until compose.py's own downstream check caught it. This
# runtime check exists so a future edit to the hardcoded zone geometry
# below can't reintroduce that exact mistake silently.
MAX_TEXT_COVERAGE_PCT = 40.0

# Default palette -- a clean, neutral blue/white scheme matching the
# common Vietnamese administrative/education-notice visual convention
# (a colored header band + dark text on white), overridable via the
# request's optional "colors" object.
DEFAULT_COLORS = {
    "header_band": "#1E3A8A",
    "kicker_text": "#FFFFFF",
    "background": "#FFFFFF",
    "title_text": "#1E293B",
    "body_text": "#334155",
    "footer_text": "#64748B",
}


def require_nonempty_text(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required and must be non-empty text")


def _base_zones() -> list[dict]:
    """Zones shared by every content type: full-bleed background + a
    colored header band + a small kicker label -- kept identical across
    all 3 templates so posters from this skill look like a coherent
    family, not 3 unrelated designs."""
    return [
        {"id": "bg", "type": "background_canvas", "x_pct": 0, "y_pct": 0, "w_pct": 100, "h_pct": 100},
        {"id": "header_band", "type": "vignette", "x_pct": 0, "y_pct": 0, "w_pct": 100, "h_pct": 15},
        {"id": "kicker", "type": "typography_frame", "x_pct": 10, "y_pct": 5, "w_pct": 80, "h_pct": 6, "text_label": "KICKER"},
    ]


def build_decree_summary(fields: dict, colors: dict) -> tuple[list[dict], dict]:
    errors: list[str] = []
    for f in ("so_hieu", "ngay_ban_hanh", "tieu_de", "noi_dung_chinh", "co_quan_ban_hanh"):
        require_nonempty_text(fields.get(f), f"fields.{f}", errors)
    if errors:
        raise ValueError(errors)

    zones = _base_zones() + [
        {"id": "so_hieu", "type": "typography_frame", "x_pct": 10, "y_pct": 18, "w_pct": 80, "h_pct": 5, "text_label": "SO_HIEU"},
        {"id": "title", "type": "typography_frame", "x_pct": 10, "y_pct": 24, "w_pct": 80, "h_pct": 9, "text_label": "TITLE"},
        {"id": "body", "type": "typography_frame", "x_pct": 10, "y_pct": 35, "w_pct": 80, "h_pct": 18, "text_label": "BODY"},
        {"id": "footer", "type": "typography_frame", "x_pct": 10, "y_pct": 88, "w_pct": 80, "h_pct": 6, "text_label": "FOOTER"},
    ]
    footer_text = fields["co_quan_ban_hanh"]
    if fields.get("hieu_luc_tu_ngay"):
        footer_text += f" · Hiệu lực từ {fields['hieu_luc_tu_ngay']}"

    content_zones = {
        "bg": {"type": "fill", "color": colors["background"]},
        "header_band": {"type": "fill", "color": colors["header_band"]},
        "kicker": {"type": "text", "text": "TÓM TẮT VĂN BẢN", "color": colors["kicker_text"], "align": "center", "font_size_pct": 60},
        "so_hieu": {"type": "text", "text": fields["so_hieu"] + f" · Ngày {fields['ngay_ban_hanh']}", "color": colors["footer_text"], "align": "left", "font_size_pct": 45},
        "title": {"type": "text", "text": fields["tieu_de"], "color": colors["title_text"], "align": "left", "font_size_pct": 40},
        "body": {"type": "text", "text": fields["noi_dung_chinh"], "color": colors["body_text"], "align": "left", "font_size_pct": 15},
        "footer": {"type": "text", "text": footer_text, "color": colors["footer_text"], "align": "left", "font_size_pct": 40},
    }
    return zones, content_zones


def build_announcement(fields: dict, colors: dict) -> tuple[list[dict], dict]:
    errors: list[str] = []
    for f in ("tieu_de", "noi_dung", "don_vi_phat_hanh"):
        require_nonempty_text(fields.get(f), f"fields.{f}", errors)
    if errors:
        raise ValueError(errors)

    zones = _base_zones() + [
        {"id": "title", "type": "typography_frame", "x_pct": 10, "y_pct": 20, "w_pct": 80, "h_pct": 12, "text_label": "TITLE"},
        {"id": "body", "type": "typography_frame", "x_pct": 10, "y_pct": 36, "w_pct": 80, "h_pct": 20, "text_label": "BODY"},
        {"id": "footer", "type": "typography_frame", "x_pct": 10, "y_pct": 88, "w_pct": 80, "h_pct": 8, "text_label": "FOOTER"},
    ]
    footer_text = fields["don_vi_phat_hanh"]
    if fields.get("thoi_han"):
        footer_text += f" · Hạn: {fields['thoi_han']}"

    content_zones = {
        "bg": {"type": "fill", "color": colors["background"]},
        "header_band": {"type": "fill", "color": colors["header_band"]},
        "kicker": {"type": "text", "text": "THÔNG BÁO", "color": colors["kicker_text"], "align": "center", "font_size_pct": 60},
        "title": {"type": "text", "text": fields["tieu_de"], "color": colors["title_text"], "align": "left", "font_size_pct": 35},
        "body": {"type": "text", "text": fields["noi_dung"], "color": colors["body_text"], "align": "left", "font_size_pct": 15},
        "footer": {"type": "text", "text": footer_text, "color": colors["footer_text"], "align": "left", "font_size_pct": 40},
    }
    return zones, content_zones


def build_contest_result(fields: dict, colors: dict) -> tuple[list[dict], dict]:
    errors: list[str] = []
    for f in ("ten_cuoc_thi", "ngay_cong_bo"):
        require_nonempty_text(fields.get(f), f"fields.{f}", errors)
    top_results = fields.get("top_results")
    if not isinstance(top_results, list) or not (1 <= len(top_results) <= 3):
        errors.append("fields.top_results must be a list of 1 to 3 objects ({hang, ten, giai_thuong})")
        top_results = []
    else:
        for i, r in enumerate(top_results):
            if not isinstance(r, dict):
                errors.append(f"fields.top_results[{i}] must be an object")
                continue
            for f in ("hang", "ten", "giai_thuong"):
                require_nonempty_text(r.get(f), f"fields.top_results[{i}].{f}", errors)
    if errors:
        raise ValueError(errors)

    zones = _base_zones() + [
        {"id": "ten_cuoc_thi", "type": "typography_frame", "x_pct": 10, "y_pct": 20, "w_pct": 80, "h_pct": 10, "text_label": "TEN_CUOC_THI"},
        {"id": "rank1", "type": "typography_frame", "x_pct": 10, "y_pct": 34, "w_pct": 80, "h_pct": 9, "text_label": "RANK1"},
        {"id": "rank2", "type": "typography_frame", "x_pct": 10, "y_pct": 45, "w_pct": 80, "h_pct": 9, "text_label": "RANK2"},
        {"id": "rank3", "type": "typography_frame", "x_pct": 10, "y_pct": 56, "w_pct": 80, "h_pct": 9, "text_label": "RANK3"},
        {"id": "footer", "type": "typography_frame", "x_pct": 10, "y_pct": 88, "w_pct": 80, "h_pct": 6, "text_label": "FOOTER"},
    ]

    def fmt(r: dict) -> str:
        return f"{r['hang']} — {r['ten']} ({r['giai_thuong']})"

    rank_texts = [fmt(r) for r in top_results] + ["Chưa công bố"] * (3 - len(top_results))

    content_zones = {
        "bg": {"type": "fill", "color": colors["background"]},
        "header_band": {"type": "fill", "color": colors["header_band"]},
        "kicker": {"type": "text", "text": "KẾT QUẢ CUỘC THI", "color": colors["kicker_text"], "align": "center", "font_size_pct": 60},
        "ten_cuoc_thi": {"type": "text", "text": fields["ten_cuoc_thi"], "color": colors["title_text"], "align": "center", "font_size_pct": 45},
        "rank1": {"type": "text", "text": rank_texts[0], "color": colors["body_text"], "align": "left", "font_size_pct": 55},
        "rank2": {"type": "text", "text": rank_texts[1], "color": colors["body_text"], "align": "left", "font_size_pct": 55},
        "rank3": {"type": "text", "text": rank_texts[2], "color": colors["body_text"], "align": "left", "font_size_pct": 55},
        "footer": {"type": "text", "text": f"Công bố ngày {fields['ngay_cong_bo']}", "color": colors["footer_text"], "align": "left", "font_size_pct": 55},
    }
    return zones, content_zones


BUILDERS = {
    "decree_summary": build_decree_summary,
    "announcement": build_announcement,
    "contest_result": build_contest_result,
}


def build(request: dict) -> tuple[dict, dict]:
    content_type = request.get("content_type")
    if content_type not in CONTENT_TYPES:
        raise ValueError([f"content_type must be one of {CONTENT_TYPES}, got {content_type!r}"])

    canvas_choice = request.get("canvas")
    if canvas_choice not in CANVAS_CHOICES:
        raise ValueError([f"canvas must be one of {sorted(CANVAS_CHOICES)}, got {canvas_choice!r}"])

    fields = request.get("fields")
    if not isinstance(fields, dict):
        raise ValueError(["fields must be an object"])

    colors = dict(DEFAULT_COLORS)
    if "colors" in request:
        if not isinstance(request["colors"], dict):
            raise ValueError(["colors must be an object if present"])
        colors.update(request["colors"])

    zones, content_zones = BUILDERS[content_type](fields, colors)

    text_coverage_pct = sum(
        (z["w_pct"] * z["h_pct"]) / 100.0 for z in zones if z["type"] == "typography_frame"
    )
    if text_coverage_pct > MAX_TEXT_COVERAGE_PCT:
        raise RuntimeError(
            f"internal error: '{content_type}' template's own zones cover {text_coverage_pct:.1f}% of the "
            f"canvas, exceeding the {MAX_TEXT_COVERAGE_PCT}% limit html-poster-composer enforces downstream -- "
            "this is a bug in this script's hardcoded zone geometry, not a caller input problem, and should "
            "never happen; please report it rather than working around it."
        )

    layout = {"canvas": {"preset": CANVAS_CHOICES[canvas_choice]}, "zones": zones}
    content = {"zones": content_zones}
    return layout, content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("request", type=Path, help="Path to a request JSON file (see assets/*_template.json)")
    parser.add_argument("--out-dir", type=Path, required=True, help="Directory to write layout.json + content.json into")
    args = parser.parse_args()

    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2
    if not isinstance(request, dict):
        print("MALFORMED: input must be a JSON object", file=sys.stderr)
        return 2

    try:
        layout, content = build(request)
    except ValueError as exc:
        errors = exc.args[0] if exc.args else [str(exc)]
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    layout_path = args.out_dir / "layout.json"
    content_path = args.out_dir / "content.json"
    layout_path.write_text(json.dumps(layout, indent=2, ensure_ascii=False), encoding="utf-8")
    content_path.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"OK: wrote {layout_path} and {content_path}")
    print(
        "NEXT STEP: render with html-poster-composer, e.g.:\n"
        f"  python <path-to-html-poster-composer>/scripts/compose.py {layout_path} {content_path} -o poster.png",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
