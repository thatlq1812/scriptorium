#!/usr/bin/env python3
"""Validate a meeting-minutes + action-item record against 2 real, checkable
conventions -- Robert's Rules of Order (minutes content) and the standard
project-management action-log/RAID-log field set (action-item tracking).
Stdlib only (json, argparse, re, datetime), local, deterministic -- no
AI/network call of any kind.

SCOPE LIMIT (read before use): this script checks STRUCTURE and REQUIRED
FIELDS only -- it does not judge whether a motion's wording is a good idea,
whether an action item is the right thing to do, or whether the underlying
decision was correct. Robert's Rules itself is explicit that minutes record
what was DONE, not what was discussed or the secretary's opinion -- this
script enforces that shape (motion text + mover + seconder + vote result),
it does not evaluate the motion's content.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_meeting_record.py <meeting_record.json>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

MEETING_TYPES = {"regular", "special", "emergency"}
VOTE_RESULTS = {"approved", "rejected", "tabled", "withdrawn"}
ACTION_STATUSES = {"open", "in_progress", "done", "blocked"}
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class RecordError(Exception):
    pass


def parse_iso_date(value: object, field: str) -> date:
    if not isinstance(value, str) or not ISO_DATE_RE.match(value):
        raise RecordError(f"{field} must be an ISO date string 'YYYY-MM-DD', got {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RecordError(f"{field} is not a real calendar date: {value!r} ({exc})") from exc


def validate_meeting(meeting: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(meeting, dict):
        return ["meeting must be an object"]

    try:
        parse_iso_date(meeting.get("date"), "meeting.date")
    except RecordError as exc:
        errors.append(str(exc))

    mtype = meeting.get("meeting_type")
    if mtype not in MEETING_TYPES:
        errors.append(f"meeting.meeting_type must be one of {sorted(MEETING_TYPES)}, got {mtype!r}")

    approved = meeting.get("previous_minutes_approved")
    if approved not in (True, False, "first_meeting"):
        errors.append(
            "meeting.previous_minutes_approved must be explicitly true, false, or the string "
            f"'first_meeting' (no prior minutes to approve) -- got {approved!r}. Robert's Rules requires "
            "this status be recorded, not left implicit."
        )

    return errors


def validate_motions(motions: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(motions, list):
        return ["motions must be a list (use [] if no motions were made this meeting)"]

    for i, m in enumerate(motions):
        if not isinstance(m, dict):
            errors.append(f"motions[{i}] must be an object")
            continue
        for field in ("text", "moved_by", "seconded_by"):
            val = m.get(field)
            if not isinstance(val, str) or not val.strip():
                errors.append(f"motions[{i}].{field} is required and must be non-empty text (Robert's Rules: exact wording + mover + seconder)")
        vote = m.get("vote_result")
        if vote not in VOTE_RESULTS:
            errors.append(f"motions[{i}].vote_result must be one of {sorted(VOTE_RESULTS)}, got {vote!r}")

    return errors


def validate_action_items(action_items: object, meeting_date: date | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(action_items, list):
        return ["action_items must be a list (use [] if no action items resulted from this meeting)"]

    seen_ids: set[str] = set()
    for i, a in enumerate(action_items):
        if not isinstance(a, dict):
            errors.append(f"action_items[{i}] must be an object")
            continue

        item_id = a.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            errors.append(f"action_items[{i}].id is required and must be a non-empty string")
        elif item_id in seen_ids:
            errors.append(f"action_items[{i}].id {item_id!r} is a duplicate -- action-log ids must be unique")
        else:
            seen_ids.add(item_id)

        desc = a.get("description")
        if not isinstance(desc, str) or not desc.strip():
            errors.append(f"action_items[{i}].description is required and must be non-empty text")

        owner = a.get("owner")
        if not isinstance(owner, str) or not owner.strip():
            errors.append(f"action_items[{i}].owner is required -- an action item with no named owner is not actionable (standard action-log/RAID-log requirement)")

        status = a.get("status")
        if status not in ACTION_STATUSES:
            errors.append(f"action_items[{i}].status must be one of {sorted(ACTION_STATUSES)}, got {status!r}")

        due_date_raw = a.get("due_date")
        try:
            due = parse_iso_date(due_date_raw, f"action_items[{i}].due_date")
            if meeting_date is not None and due < meeting_date:
                errors.append(
                    f"action_items[{i}].due_date {due_date_raw!r} is before the meeting date {meeting_date.isoformat()!r} "
                    "-- an action item cannot be due before it was assigned"
                )
        except RecordError as exc:
            errors.append(str(exc))

    return errors


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["input must be a JSON object with 'meeting', 'motions', 'action_items' keys"]

    meeting = record.get("meeting")
    errors.extend(validate_meeting(meeting))

    meeting_date: date | None = None
    if isinstance(meeting, dict):
        try:
            meeting_date = parse_iso_date(meeting.get("date"), "meeting.date")
        except RecordError:
            meeting_date = None

    if "motions" not in record:
        errors.append("motions key is required (use [] if no motions were made this meeting -- do not omit the key)")
    else:
        errors.extend(validate_motions(record.get("motions")))

    if "action_items" not in record:
        errors.append("action_items key is required (use [] if no action items resulted -- do not omit the key)")
    else:
        errors.extend(validate_action_items(record.get("action_items"), meeting_date))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to a meeting-record JSON file (see assets/meeting_record_template.json)")
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
        "NOTE: this checks minutes STRUCTURE (Robert's Rules content shape: meeting type, prior-minutes "
        "approval status, motion wording/mover/seconder/vote) and action-item STRUCTURE (id/description/"
        "owner/due-date/status, the standard action-log/RAID-log field set) only -- it does not judge "
        "whether a motion or action item is a good decision, and it is not a legal-validity check on the "
        "meeting itself.",
        file=sys.stderr,
    )

    errors = validate(data)

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    motions_n = len(data.get("motions", []))
    actions_n = len(data.get("action_items", []))
    print(f"OK: meeting record well-formed -- {motions_n} motion(s), {actions_n} action item(s), no structural issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
