#!/usr/bin/env python3
"""Validate the STRUCTURE of a marketing campaign brief against a real,
widely-corroborated 9-element convention (objective+deadline, audience, key
message, channels+role, deliverables, timeline, budget+split, KPIs,
mandatories), plus an optional per-funnel-stage objective/metric check
supporting either a 3-stage (TOFU/MOFU/BOFU) or 4-stage (+loyalty) funnel.
Stdlib only (json, argparse, datetime), local, deterministic -- no
AI/network call of any kind.

SCOPE LIMIT (read before use): this checks STRUCTURE and BUDGET ARITHMETIC
only -- it does not judge whether the objective is realistic, whether the
audience definition is good, or whether the creative strategy will work.
Content/strategy judgment is a human/marketer task.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_campaign_brief.py <brief.json>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

FUNNEL_STAGES = {"awareness", "consideration", "conversion", "loyalty"}
KEY_MESSAGE_MAX_CHARS = 200


class RecordError(Exception):
    pass


def parse_iso_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise RecordError(f"{field} must be an ISO date string 'YYYY-MM-DD', got {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RecordError(f"{field} is not a real calendar date: {value!r} ({exc})") from exc


def require_nonempty_text(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required and must be non-empty text")


def validate_objective(obj: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(obj, dict):
        return ["objective must be an object with 'statement' and 'deadline'"]
    require_nonempty_text(obj.get("statement"), "objective.statement", errors)
    try:
        parse_iso_date(obj.get("deadline"), "objective.deadline")
    except RecordError as exc:
        errors.append(str(exc))
    return errors


def validate_channels(channels: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(channels, list) or not channels:
        return ["channels must be a non-empty list -- a brief naming no channel can't be executed"]
    for i, c in enumerate(channels):
        if not isinstance(c, dict):
            errors.append(f"channels[{i}] must be an object")
            continue
        require_nonempty_text(c.get("name"), f"channels[{i}].name", errors)
        require_nonempty_text(c.get("role"), f"channels[{i}].role", errors)
    return errors


def validate_deliverables(deliverables: object) -> list[str]:
    if not isinstance(deliverables, list) or not deliverables:
        return ["deliverables must be a non-empty list -- a brief with no concrete asset list can't be executed"]
    errors: list[str] = []
    for i, d in enumerate(deliverables):
        if not isinstance(d, str) or not d.strip():
            errors.append(f"deliverables[{i}] must be non-empty text")
    return errors


def validate_timeline(timeline: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(timeline, list) or not timeline:
        return ["timeline must be a non-empty list -- a brief with no key dates can't be executed"]
    for i, t in enumerate(timeline):
        if not isinstance(t, dict):
            errors.append(f"timeline[{i}] must be an object")
            continue
        require_nonempty_text(t.get("milestone"), f"timeline[{i}].milestone", errors)
        try:
            parse_iso_date(t.get("date"), f"timeline[{i}].date")
        except RecordError as exc:
            errors.append(str(exc))
    return errors


def validate_budget(budget: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(budget, dict):
        return ["budget must be an object with 'total', 'currency', and 'split'"]

    total = budget.get("total")
    if not isinstance(total, (int, float)) or isinstance(total, bool) or total <= 0:
        errors.append(f"budget.total must be a positive number, got {total!r}")
    require_nonempty_text(budget.get("currency"), "budget.currency", errors)

    split = budget.get("split")
    if not isinstance(split, list) or not split:
        errors.append("budget.split must be a non-empty list -- a total with no channel breakdown isn't actionable")
        return errors

    running_sum = 0.0
    split_valid = True
    for i, s in enumerate(split):
        if not isinstance(s, dict):
            errors.append(f"budget.split[{i}] must be an object")
            split_valid = False
            continue
        require_nonempty_text(s.get("channel"), f"budget.split[{i}].channel", errors)
        amount = s.get("amount")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount < 0:
            errors.append(f"budget.split[{i}].amount must be a non-negative number, got {amount!r}")
            split_valid = False
        else:
            running_sum += amount

    if split_valid and isinstance(total, (int, float)) and not isinstance(total, bool):
        if abs(running_sum - total) > 1e-6:
            errors.append(f"budget.split amounts sum to {running_sum!r} but budget.total is {total!r} -- they must match")

    return errors


def validate_kpis(kpis: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(kpis, list) or not kpis:
        return ["kpis must be a non-empty list -- a brief with no success metric can't be judged"]
    for i, k in enumerate(kpis):
        if not isinstance(k, dict):
            errors.append(f"kpis[{i}] must be an object")
            continue
        require_nonempty_text(k.get("metric"), f"kpis[{i}].metric", errors)
        if k.get("target") is None:
            errors.append(f"kpis[{i}].target is required (a metric with no target isn't measurable)")
        require_nonempty_text(k.get("window"), f"kpis[{i}].window", errors)
    return errors


def validate_funnel_stages(stages: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(stages, list):
        return ["funnel_stages must be a list if present"]
    seen: set[str] = set()
    for i, s in enumerate(stages):
        if not isinstance(s, dict):
            errors.append(f"funnel_stages[{i}] must be an object")
            continue
        stage = s.get("stage")
        if stage not in FUNNEL_STAGES:
            errors.append(f"funnel_stages[{i}].stage must be one of {sorted(FUNNEL_STAGES)} (supports both a 3-stage and 4-stage funnel), got {stage!r}")
        elif stage in seen:
            errors.append(f"funnel_stages[{i}].stage {stage!r} is a duplicate -- each stage should appear at most once")
        else:
            seen.add(stage)
        require_nonempty_text(s.get("objective"), f"funnel_stages[{i}].objective", errors)
        require_nonempty_text(s.get("metric"), f"funnel_stages[{i}].metric", errors)
    return errors


def validate(record: dict) -> list[str]:
    errors: list[str] = []

    require_nonempty_text(record.get("campaign_name"), "campaign_name", errors)

    if "objective" not in record:
        errors.append("objective key is required")
    else:
        errors.extend(validate_objective(record.get("objective")))

    require_nonempty_text(record.get("audience"), "audience", errors)

    key_message = record.get("key_message")
    require_nonempty_text(key_message, "key_message", errors)
    if isinstance(key_message, str) and len(key_message) > KEY_MESSAGE_MAX_CHARS:
        errors.append(
            f"key_message is {len(key_message)} characters -- a real one-sentence key message is expected to "
            f"stay well under {KEY_MESSAGE_MAX_CHARS}; this reads more like a paragraph than a key message"
        )

    if "channels" not in record:
        errors.append("channels key is required")
    else:
        errors.extend(validate_channels(record.get("channels")))

    if "deliverables" not in record:
        errors.append("deliverables key is required")
    else:
        errors.extend(validate_deliverables(record.get("deliverables")))

    if "timeline" not in record:
        errors.append("timeline key is required")
    else:
        errors.extend(validate_timeline(record.get("timeline")))

    if "budget" not in record:
        errors.append("budget key is required")
    else:
        errors.extend(validate_budget(record.get("budget")))

    if "kpis" not in record:
        errors.append("kpis key is required")
    else:
        errors.extend(validate_kpis(record.get("kpis")))

    if "mandatories" not in record:
        errors.append("mandatories key is required (use [] if there are genuinely none -- do not omit the key)")
    elif not isinstance(record.get("mandatories"), list):
        errors.append("mandatories must be a list")

    if "funnel_stages" in record:
        errors.extend(validate_funnel_stages(record.get("funnel_stages")))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("brief", type=Path, help="Path to a campaign-brief JSON file (see assets/campaign_brief_template.json)")
    args = parser.parse_args()

    try:
        data = json.loads(args.brief.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("MALFORMED: input must be a JSON object", file=sys.stderr)
        return 2

    print(
        "NOTE: this checks campaign-brief STRUCTURE (the 9-element convention: objective/audience/key-message/"
        "channels/deliverables/timeline/budget/KPIs/mandatories) and budget-split ARITHMETIC only, plus an "
        "optional per-funnel-stage objective/metric check -- it does not judge whether the objective is "
        "realistic or the creative strategy will work.",
        file=sys.stderr,
    )

    errors = validate(data)

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK: campaign brief structurally complete, no issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
