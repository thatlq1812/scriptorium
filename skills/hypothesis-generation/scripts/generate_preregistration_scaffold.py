#!/usr/bin/env python3
"""Fill assets/preregistration_scaffold_template.md from a hypothesis record
JSON file (see assets/hypothesis_record_template.json). Stdlib only, local,
deterministic. Produces a SCAFFOLD, not a finished preregistration — the
design/analysis-plan section (§5) is intentionally left as <TODO> for a
human/agent to fill in before touching outcome data.

Usage:
    python generate_preregistration_scaffold.py record.json -o preregistration.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "assets" / "preregistration_scaffold_template.md"


def render_candidates(candidates: list[dict]) -> str:
    lines = []
    for c in candidates:
        lines.append(f"- **{c.get('id', '?')}** ({c.get('class', 'unclassified')}, status: {c.get('status', '?')}): {c.get('statement', '')}")
    return "\n".join(lines) if lines else "<none provided>"


def render_predictions(predictions: list[dict]) -> str:
    lines = []
    for p in predictions:
        rivals = ", ".join(p.get("contrasted_with", [])) or "none listed"
        lines.append(
            f"- For **{p.get('candidate_id', '?')}**: observe {p.get('observable', '')} — "
            f"expect {p.get('expected_pattern', '')}; falsified by {p.get('falsifying_result', '')} "
            f"(contrasted with: {rivals})"
        )
    return "\n".join(lines) if lines else "<none provided>"


def fill_scaffold(record: dict, template: str) -> str:
    obs = record.get("observation", {})
    auth = record.get("authorization", {})
    out = template
    out = out.replace("<research question>", record.get("research_question", "<missing>"))
    out = out.replace("<date>", dt.date.today().isoformat())
    out = out.replace("<research_question>", record.get("research_question", "<missing>"))
    out = out.replace("<claim_type>", record.get("claim_type", "<missing>"))
    out = out.replace("<observation.description>", obs.get("description", "<missing>"))
    out = out.replace("<observation.source>", obs.get("source", "<missing>"))
    out = out.replace("<observation.population_or_system>", obs.get("population_or_system", "<missing>"))
    out = out.replace("<observation.unit_of_observation>", obs.get("unit_of_observation", "<missing>"))
    out = out.replace("<observation.uncertainty>", obs.get("uncertainty", "<missing>"))
    out = out.replace("<observation.was_pattern_expected_or_post_hoc>", obs.get("was_pattern_expected_or_post_hoc", "<missing>"))
    out = out.replace(
        '<For each candidate: id, statement, class — all still labeled "candidate">',
        render_candidates(record.get("candidates", [])),
    )
    out = out.replace(
        "<For each prediction: which candidate, the observable, the expected pattern,\n"
        "what result would falsify it, and which rival it's contrasted against>",
        render_predictions(record.get("predictions", [])),
    )
    out = out.replace("<authorization.accountable_human>", str(auth.get("accountable_human", "<missing>")))
    out = out.replace("<authorization.data_sensitivity>", str(auth.get("data_sensitivity", "<missing>")))
    out = out.replace("<authorization.required_reviews>", ", ".join(auth.get("required_reviews", [])) or "<missing>")
    out = out.replace("<authorization.unresolved_blocks>", str(auth.get("unresolved_blocks", "<missing>")))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to a hypothesis record JSON file")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    scaffold = fill_scaffold(record, template)

    if args.output.exists() and not args.force:
        print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
        return 2

    args.output.write_text(scaffold, encoding="utf-8")
    print(f"OK: wrote scaffold to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
