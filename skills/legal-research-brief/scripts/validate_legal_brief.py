#!/usr/bin/env python3
"""Validate a legal research brief JSON record against a strict-grounding
requirement: every factual claim, statutory ground, and application-of-law
statement must cite at least one caller-supplied source, and every cited
source id must actually exist in the supplied sources list. Stdlib only
(json, argparse), local, deterministic -- no AI/LLM/network call of any
kind, and this script never searches the web or any legal database itself.

Why this exists: an LLM can hallucinate a statute number, a case citation,
or a fact that was never in the file -- exactly the fabricated-citation
risk this project's citation-management skill was built to avoid for
academic sources. This is the same discipline applied to legal research:
the brief may only assert what a supplied source actually says, and every
such assertion must be traceable back to a real, caller-provided source.

The output schema (cau_hoi_chinh / su_kien_da_xac_minh / thieu_sot_gia_dinh
/ can_cu_phap_ly / phan_tich_ap_dung / quan_diem_trai_chieu / danh_gia_rui_ro)
mirrors a structured legal-opinion format elicited from
outside_research/research_01_result_01.md's "Output Schema Component" table.

Exit codes: 0 = valid, 1 = validation errors found, 2 = malformed input.

Usage:
    python validate_legal_brief.py sources.json brief.json [--render brief.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

# These 3 sections make factual/legal assertions and MUST be grounded.
# The other 4 sections are framing/analysis/judgment and are not
# citation-checked (a risk assessment or a "what's missing" note is not a
# factual claim being sourced -- it's the human/agent's own analysis).
GROUNDED_SECTIONS = ["su_kien_da_xac_minh", "can_cu_phap_ly", "phan_tich_ap_dung"]
UNGROUNDED_TEXT_FIELDS = ["thieu_sot_gia_dinh", "quan_diem_trai_chieu", "danh_gia_rui_ro"]


class BriefError(Exception):
    pass


def load_sources(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BriefError(f"cannot read sources file: {exc}") from exc
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise BriefError("sources.json must have a non-empty 'sources' list")
    ids = set()
    for i, s in enumerate(sources):
        if not isinstance(s, dict) or not s.get("id"):
            raise BriefError(f"sources[{i}] must be an object with a non-empty 'id'")
        if s["id"] in ids:
            raise BriefError(f"duplicate source id: {s['id']!r}")
        ids.add(s["id"])
    return ids


def validate(brief: dict, valid_source_ids: set[str]) -> list[str]:
    errors: list[str] = []

    if not brief.get("cau_hoi_chinh"):
        errors.append("cau_hoi_chinh is required")

    for field in UNGROUNDED_TEXT_FIELDS:
        if not brief.get(field):
            errors.append(f"{field} is required (even if the answer is 'none identified', state that explicitly -- don't omit the field)")

    for section in GROUNDED_SECTIONS:
        items = brief.get(section)
        if not isinstance(items, list) or not items:
            errors.append(f"{section} must be a non-empty list")
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict) or not item.get("noi_dung"):
                errors.append(f"{section}[{i}]: noi_dung is required")
                continue
            nguon = item.get("nguon")
            if not isinstance(nguon, list) or not nguon:
                errors.append(f"{section}[{i}] ({item['noi_dung'][:40]!r}...): nguon (source citation) is required -- this is a grounded section, every claim must cite a source")
                continue
            for src_id in nguon:
                if src_id not in valid_source_ids:
                    errors.append(f"{section}[{i}]: cites source id {src_id!r} which does not exist in sources.json -- likely a fabricated or mistyped citation")

    return errors


def to_markdown(brief: dict, sources_by_id: dict) -> str:
    def cite(nguon: list[str]) -> str:
        return " [" + ", ".join(sources_by_id.get(s, s) for s in nguon) + "]"

    lines = [
        f"# Legal Research Brief",
        "",
        f"## Câu hỏi pháp lý chính",
        "",
        brief["cau_hoi_chinh"],
        "",
        "## Sự kiện đã xác minh",
        "",
    ]
    for item in brief["su_kien_da_xac_minh"]:
        lines.append(f"- {item['noi_dung']}{cite(item['nguon'])}")
    lines.extend(["", "## Thiếu sót / giả định", "", brief["thieu_sot_gia_dinh"], "", "## Căn cứ pháp lý", ""])
    for item in brief["can_cu_phap_ly"]:
        lines.append(f"- {item['noi_dung']}{cite(item['nguon'])}")
    lines.extend(["", "## Phân tích áp dụng", ""])
    for item in brief["phan_tich_ap_dung"]:
        lines.append(f"- {item['noi_dung']}{cite(item['nguon'])}")
    lines.extend([
        "", "## Quan điểm trái chiều", "", brief["quan_diem_trai_chieu"],
        "", "## Đánh giá rủi ro", "", brief["danh_gia_rui_ro"],
        "", "## Nguồn", "",
    ])
    for sid, label in sources_by_id.items():
        lines.append(f"- **{sid}**: {label}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sources", type=Path, help="Path to a sources JSON file (see assets/sources_template.json)")
    parser.add_argument("brief", type=Path, help="Path to a legal brief JSON file (see assets/legal_brief_template.json)")
    parser.add_argument("--render", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        valid_source_ids = load_sources(args.sources)
    except BriefError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    try:
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(brief, dict):
        print("MALFORMED: top-level brief JSON must be an object", file=sys.stderr)
        return 2

    errors = validate(brief, valid_source_ids)
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: every grounded claim cites a real, declared source. This confirms grounding/structure only, not legal correctness.")

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        sources = json.loads(args.sources.read_text(encoding="utf-8"))["sources"]
        sources_by_id = {s["id"]: s["label"] for s in sources}
        args.render.write_text(to_markdown(brief, sources_by_id), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
