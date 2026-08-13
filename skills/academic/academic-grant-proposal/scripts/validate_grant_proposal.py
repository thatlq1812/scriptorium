#!/usr/bin/env python3
"""Validate a grant-proposal JSON record for structural completeness and
internal consistency against a caller-declared budget table. Stdlib only
(json, argparse), local, deterministic -- no AI/LLM/network call of any
kind, and this script never drafts, scores, or judges the scientific merit
of a proposal.

Why this exists: funding bodies reject proposals for missing/boilerplate
required sections and for budget justifications that don't tie back to the
actual budget request -- both are mechanically checkable before a human
ever reviews the science. This mirrors legal-research-brief's grounding
discipline (every claim must trace to a real declared source) applied to
grant structure: every budget-justification narrative must trace to a real
declared budget line item, and no required section may be empty.

The 5-section structure (specific_aims, significance, approach,
budget_justification, timeline) is the common structural core shared by
NIH's SF424 (R&R) Application Guide (Specific Aims / Significance /
Approach as separate required attachments for an R01-type research
narrative, https://grants.nih.gov/grants/how-to-apply-application-guide.html)
and NSF's Proposal & Award Policies & Procedures Guide (PAPPG) Project
Description + mandatory Budget Justification
(https://www.nsf.gov/policies/pappg). This skill does not encode either
body's full section set (e.g. NIH's separate "Innovation" section, NSF's
Broader Impacts) -- see "What this skill does NOT do" in SKILL.md.

Exit codes: 0 = valid, 1 = validation errors found, 2 = malformed input.

Usage:
    python validate_grant_proposal.py <budget.json> <proposal.json> [--render proposal.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_TEXT_SECTIONS = ["specific_aims", "significance", "approach"]


class ProposalError(Exception):
    pass


def load_budget(path: Path) -> dict[str, dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProposalError(f"cannot read budget file: {exc}") from exc
    if not isinstance(data, dict):
        raise ProposalError("budget.json top-level must be an object")
    line_items = data.get("line_items")
    if not isinstance(line_items, list) or not line_items:
        raise ProposalError("budget.json must have a non-empty 'line_items' list")
    by_id: dict[str, dict] = {}
    for i, item in enumerate(line_items):
        if not isinstance(item, dict) or not item.get("id"):
            raise ProposalError(f"line_items[{i}] must be an object with a non-empty 'id'")
        item_id = item["id"]
        if item_id in by_id:
            raise ProposalError(f"duplicate budget line item id: {item_id!r}")
        if not item.get("category"):
            raise ProposalError(f"line_items[{i}] ({item_id!r}): 'category' is required")
        amount = item.get("amount")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
            raise ProposalError(f"line_items[{i}] ({item_id!r}): 'amount' must be a positive number")
        by_id[item_id] = item
    return by_id


def load_proposal(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProposalError(f"cannot read proposal file: {exc}") from exc
    if not isinstance(data, dict):
        raise ProposalError("proposal.json top-level must be an object")
    return data


def validate(proposal: dict, budget_ids: set[str]) -> list[str]:
    errors: list[str] = []

    if not proposal.get("title"):
        errors.append("title is required")

    for field in REQUIRED_TEXT_SECTIONS:
        value = proposal.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required and must be a non-empty string")

    timeline = proposal.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        errors.append("timeline must be a non-empty list")
    else:
        for i, milestone in enumerate(timeline):
            if not isinstance(milestone, dict) or not milestone.get("milestone") or not milestone.get("period"):
                errors.append(f"timeline[{i}] must be an object with non-empty 'milestone' and 'period'")

    budget_justification = proposal.get("budget_justification")
    if not isinstance(budget_justification, list) or not budget_justification:
        errors.append("budget_justification must be a non-empty list")
    else:
        referenced_ids: set[str] = set()
        for i, entry in enumerate(budget_justification):
            if not isinstance(entry, dict) or not entry.get("narrative"):
                errors.append(f"budget_justification[{i}]: 'narrative' is required")
                continue
            line_item_id = entry.get("line_item_id")
            if not line_item_id:
                errors.append(f"budget_justification[{i}]: 'line_item_id' is required")
                continue
            if line_item_id not in budget_ids:
                errors.append(
                    f"budget_justification[{i}]: references line_item_id {line_item_id!r} "
                    f"which does not exist in budget.json -- likely a fabricated or mistyped line item"
                )
                continue
            referenced_ids.add(line_item_id)

        unjustified = budget_ids - referenced_ids
        if unjustified:
            errors.append(
                f"budget line item(s) with no budget_justification entry: {sorted(unjustified)} "
                f"-- every declared budget line item must be justified"
            )

    return errors


def to_markdown(proposal: dict, budget_by_id: dict[str, dict]) -> str:
    lines = [
        f"# {proposal['title']}",
        "",
        "## Specific Aims",
        "",
        proposal["specific_aims"],
        "",
        "## Significance",
        "",
        proposal["significance"],
        "",
        "## Approach",
        "",
        proposal["approach"],
        "",
        "## Timeline",
        "",
    ]
    for m in proposal["timeline"]:
        lines.append(f"- **{m['period']}**: {m['milestone']}")
    lines.extend(["", "## Budget Justification", ""])
    for entry in proposal["budget_justification"]:
        item = budget_by_id[entry["line_item_id"]]
        lines.append(
            f"- **{item['category']}** (${item['amount']:,.2f}, {entry['line_item_id']}): {entry['narrative']}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("budget", type=Path, help="Path to a budget JSON file (see assets/budget_template.json)")
    parser.add_argument("proposal", type=Path, help="Path to a proposal JSON file (see assets/proposal_template.json)")
    parser.add_argument("--render", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        budget_by_id = load_budget(args.budget)
    except ProposalError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    try:
        proposal = load_proposal(args.proposal)
    except ProposalError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    errors = validate(proposal, set(budget_by_id.keys()))
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        "VALID: all 5 required sections present and non-empty, every budget "
        "justification traces to a real declared budget line item, and every "
        "budget line item is justified. This confirms structure/consistency "
        "only, not scientific merit or funder-specific compliance."
    )

    if args.render:
        if args.render.exists() and not args.force:
            print(f"REFUSED: {args.render} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.render.write_text(to_markdown(proposal, budget_by_id), encoding="utf-8")
        print(f"OK: rendered to {args.render}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
