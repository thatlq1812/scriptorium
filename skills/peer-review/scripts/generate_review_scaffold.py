#!/usr/bin/env python3
"""Fill assets/review_scaffold_template.md from a validated review-intake
JSON file. Stdlib only, local, deterministic. Refuses to run unless the
intake would pass validate_review_intake.py (READY_FOR_LOCAL_REVIEW) —
this is a private working-draft scaffold, not a finished review.

Usage:
    python generate_review_scaffold.py completed-intake.json -o private-review.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_review_intake import validate as validate_intake  # noqa: E402

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "assets" / "review_scaffold_template.md"


def fill_scaffold(intake: dict, template: str) -> str:
    acc = intake.get("accountability", {})
    out = template
    out = out.replace("<target_venue>", intake.get("target_venue", "<missing>"))
    out = out.replace("<submission_type>", intake.get("submission_type", "<missing>"))
    out = out.replace("<review_question>", intake.get("review_question", "<missing>"))
    out = out.replace("<competence_areas>", ", ".join(acc.get("competence_areas", [])) or "<missing>")
    out = out.replace("<competence_limits>", acc.get("competence_limits", "<missing>"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("intake", type=Path, help="Path to a completed review-intake JSON file")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        intake = json.loads(args.intake.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    reasons = validate_intake(intake)
    if reasons:
        print("REFUSED: intake is not READY_FOR_LOCAL_REVIEW, run validate_review_intake.py to see why:", file=sys.stderr)
        for r in reasons:
            print(f"  - {r}", file=sys.stderr)
        return 1

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    scaffold = fill_scaffold(intake, template)

    if args.output.exists() and not args.force:
        print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
        return 2

    args.output.write_text(scaffold, encoding="utf-8")
    print(f"OK: wrote private review scaffold to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
