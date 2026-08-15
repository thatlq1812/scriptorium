#!/usr/bin/env python3
"""Validate the STRUCTURE of a Standard Operating Procedure (SOP) document
against a real, widely-corroborated convention -- header/purpose/scope/
roles-responsibilities/numbered-steps/revision-history-with-approval.
Stdlib only (json, argparse, datetime), local, deterministic -- no
AI/network call of any kind.

SCOPE LIMIT (read before use): this script checks STRUCTURE and REQUIRED
FIELDS only -- it does not judge whether the procedure itself is correct,
safe, or well-designed. A syntactically complete SOP for a bad process is
still "structurally valid" by this script's own definition; content
judgment is a human/domain-expert task.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_sop.py <sop_record.json>
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


def validate_roles(roles: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(roles, list) or not roles:
        return ["roles_responsibilities must be a non-empty list -- an SOP with no named responsible role is not a real SOP"]
    for i, r in enumerate(roles):
        if not isinstance(r, dict):
            errors.append(f"roles_responsibilities[{i}] must be an object")
            continue
        require_nonempty_text(r.get("role"), f"roles_responsibilities[{i}].role", errors)
        require_nonempty_text(r.get("responsibility"), f"roles_responsibilities[{i}].responsibility", errors)
    return errors


def validate_steps(steps: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(steps, list) or not steps:
        return ["steps must be a non-empty list -- an SOP with no procedural steps is not a real SOP"]

    seen_numbers: list[int] = []
    for i, s in enumerate(steps):
        if not isinstance(s, dict):
            errors.append(f"steps[{i}] must be an object")
            continue
        number = s.get("number")
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            errors.append(f"steps[{i}].number must be a positive integer, got {number!r}")
        else:
            seen_numbers.append(number)
        require_nonempty_text(s.get("text"), f"steps[{i}].text", errors)

    expected = list(range(1, len(steps) + 1))
    if sorted(seen_numbers) != expected:
        errors.append(
            f"steps must be numbered sequentially starting at 1 with no gaps or duplicates -- got numbers "
            f"{sorted(seen_numbers)}, expected {expected}"
        )

    return errors


def validate_revision_history(history: object, top_level_version: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(history, list) or not history:
        return ["revision_history must be a non-empty list -- at minimum the initial version must be logged"]

    for i, rev in enumerate(history):
        if not isinstance(rev, dict):
            errors.append(f"revision_history[{i}] must be an object")
            continue
        require_nonempty_text(rev.get("version"), f"revision_history[{i}].version", errors)
        require_nonempty_text(rev.get("description"), f"revision_history[{i}].description", errors)
        require_nonempty_text(rev.get("approved_by"), f"revision_history[{i}].approved_by", errors)
        try:
            parse_iso_date(rev.get("date"), f"revision_history[{i}].date")
        except RecordError as exc:
            errors.append(str(exc))

    if isinstance(history, list) and history and isinstance(history[-1], dict):
        last_version = history[-1].get("version")
        if last_version is not None and top_level_version is not None and last_version != top_level_version:
            errors.append(
                f"revision_history's last entry has version {last_version!r} but the document's top-level "
                f"version is {top_level_version!r} -- the log's latest entry should match the current version"
            )

    return errors


def validate(record: dict) -> list[str]:
    errors: list[str] = []

    require_nonempty_text(record.get("document_id"), "document_id", errors)
    require_nonempty_text(record.get("version"), "version", errors)
    try:
        parse_iso_date(record.get("effective_date"), "effective_date")
    except RecordError as exc:
        errors.append(str(exc))
    require_nonempty_text(record.get("purpose"), "purpose", errors)
    require_nonempty_text(record.get("scope"), "scope", errors)

    if "roles_responsibilities" not in record:
        errors.append("roles_responsibilities key is required")
    else:
        errors.extend(validate_roles(record.get("roles_responsibilities")))

    if "steps" not in record:
        errors.append("steps key is required")
    else:
        errors.extend(validate_steps(record.get("steps")))

    if "revision_history" not in record:
        errors.append("revision_history key is required")
    else:
        errors.extend(validate_revision_history(record.get("revision_history"), record.get("version")))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to an SOP-record JSON file (see assets/sop_record_template.json)")
    args = parser.parse_args()

    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("MALFORMED: input must be a JSON object", file=sys.stderr)
        return 2

    print(
        "NOTE: this checks SOP STRUCTURE only (header/purpose/scope/roles/numbered-steps/revision-history-"
        "with-approval, per a widely-corroborated documentation convention) -- it does not judge whether "
        "the procedure itself is correct, safe, or well-designed.",
        file=sys.stderr,
    )

    errors = validate(data)

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    steps_n = len(data.get("steps", []))
    roles_n = len(data.get("roles_responsibilities", []))
    print(f"OK: SOP structurally complete -- {roles_n} role(s), {steps_n} step(s), no structural issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
