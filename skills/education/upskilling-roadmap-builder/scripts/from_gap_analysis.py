#!/usr/bin/env python3
"""Convert a knowledge-gap-analyzer JSON report into this skill's own
skills_gap.json input shape, so the two skills chain into a real pipeline:

    self-assessment -> knowledge-gap-analyzer (diagnostic report,
    confidence-scored) -> from_gap_analysis.py (this script) ->
    build_roadmap.py (actionable day-by-day schedule)

Mechanical conversion only -- never invents a weight. Every skill landing
in the roadmap's target_skills gets the SAME caller-declared weight (no
per-skill severity ranking exists in the source report beyond raw
confidence numbers, and inventing a formula to turn "confidence 1 vs 2"
into "weight 4 vs 3" would be exactly the kind of guessed methodology
knowledge-gap-analyzer's own SKILL.md explicitly refuses to do -- this
script inherits that refusal rather than working around it).

Usage:
    python from_gap_analysis.py <gap_report.json> --weight N -o skills_gap.json

Exit 0 = converted, 1 = report has zero gaps (nothing to schedule -- not
an error, just nothing to convert), 2 = malformed input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_KEYS = {"target_role", "meets_bar", "below_threshold", "not_assessed", "gap_count", "ready"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gap_report_path")
    parser.add_argument("--weight", type=int, default=2, help="Weight (1-5) applied to every gap skill -- knowledge-gap-analyzer's confidence scores are ordinal, not a weight formula, so this is a single caller-declared value, not derived per-skill.")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not 1 <= args.weight <= 5:
        print(f"ERROR: --weight must be 1-5, got {args.weight}", file=sys.stderr)
        return 2

    path = Path(args.gap_report_path)
    if not path.exists():
        print(f"ERROR: gap report not found: {path}", file=sys.stderr)
        return 2
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        return 2

    if not isinstance(report, dict) or not REQUIRED_KEYS.issubset(report):
        print(f"ERROR: gap report must be a knowledge-gap-analyzer --json output with keys {sorted(REQUIRED_KEYS)}", file=sys.stderr)
        return 2

    if report["ready"] or report["gap_count"] == 0:
        print("OK: gap report shows no gaps (ready=true) -- nothing to convert, no roadmap needed.")
        return 1

    current_skills = [entry["name"] for entry in report["meets_bar"]]
    target_skills = (
        [{"name": entry["name"], "weight": args.weight} for entry in report["below_threshold"]]
        + [{"name": name, "weight": args.weight} for name in report["not_assessed"]]
    )
    # target_skills must be the FULL target-role list for upskilling-roadmap-builder's own
    # gap computation to reproduce the same gap -- meets_bar entries go in too, at weight 0
    # equivalent (they're already held, so they'll be excluded by that skill's own current_skills match).
    target_skills += [{"name": entry["name"], "weight": args.weight} for entry in report["meets_bar"]]

    skills_gap = {
        "target_role": report["target_role"],
        "current_skills": current_skills,
        "target_skills": target_skills,
    }

    out_path = Path(args.output)
    if out_path.exists() and not args.force:
        print(f"ERROR: {out_path} already exists. Use --force to overwrite.", file=sys.stderr)
        return 2
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(skills_gap, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    print(f"Converted {report['gap_count']} gap skill(s) from {path} -> {out_path}")
    print(f"  target_role: {report['target_role']}")
    print(f"  current_skills (already meets bar): {len(current_skills)}")
    print(f"  gap skills to schedule: {len(report['below_threshold']) + len(report['not_assessed'])}")
    print("Next: python scripts/build_roadmap.py <output> --days N")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
