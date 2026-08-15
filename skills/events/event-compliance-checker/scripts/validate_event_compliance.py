#!/usr/bin/env python3
"""Check a caller-declared event record against Vietnam's Nghị định
144/2020/NĐ-CP (performing-arts/public-event activities) -- the real
2-pathway model (Điều 8/9 notification vs. Điều 8/10 approval), lead-time
requirements, eligibility conditions, and change-notice deadlines. Stdlib
only (json, argparse, datetime), local, deterministic -- no AI/network call.

CRITICAL SCOPE LIMIT (read before use): this checks the STRUCTURAL/NUMERIC
rules honestly deterministic from a caller-declared record -- it does NOT
verify the substance of security/fire-safety compliance (Điều 10 khoản 1b
only references "quy định của pháp luật" generically, without naming the
specific fire-safety/security decree this project has separately verified),
does NOT constitute legal advice, and working-day counts exclude Saturday/
Sunday only -- Vietnamese public holidays are NOT accounted for (a real,
documented limitation, not silently assumed away).

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_event_compliance.py <event_record.json>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

PATHWAYS = {"notification", "approval"}
ENTITY_TYPES = {"public_institution", "professional_association", "registered_business"}
NOTIFICATION_MIN_WORKING_DAYS = 5   # Dieu 9 khoan 4
APPROVAL_MIN_WORKING_DAYS = 7        # Dieu 10 khoan 4a
APPROVAL_RESPONSE_MAX_WORKING_DAYS = 5  # Dieu 10 khoan 4c
CHANGE_NOTICE_MIN_WORKING_DAYS = 2   # Dieu 10 khoan 4d/4d


class RecordError(Exception):
    pass


def parse_iso_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise RecordError(f"{field} must be an ISO date string 'YYYY-MM-DD', got {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RecordError(f"{field} is not a real calendar date: {value!r} ({exc})") from exc


def working_days_between(start: date, end: date) -> int:
    """Count Mon-Fri days strictly between start and end (exclusive of
    start, inclusive of end if end is a weekday) -- weekends excluded,
    Vietnamese public holidays NOT accounted for (documented limitation)."""
    if end < start:
        return -working_days_between(end, start)
    count = 0
    d = start
    while d < end:
        d += timedelta(days=1)
        if d.weekday() < 5:  # Mon=0 .. Fri=4
            count += 1
    return count


def validate_event(event: dict) -> tuple[list[str], date | None, date | None, str | None]:
    errors: list[str] = []
    pathway = event.get("pathway")
    if pathway not in PATHWAYS:
        errors.append(f"event.pathway must be one of {sorted(PATHWAYS)}, got {pathway!r}")

    submission_date = planned_date = None
    try:
        planned_date = parse_iso_date(event.get("planned_date"), "event.planned_date")
    except RecordError as exc:
        errors.append(str(exc))
    try:
        submission_date = parse_iso_date(event.get("submission_date"), "event.submission_date")
    except RecordError as exc:
        errors.append(str(exc))

    if planned_date is not None and submission_date is not None:
        if submission_date > planned_date:
            errors.append("event.submission_date is after event.planned_date -- not possible")
        else:
            lead_days = working_days_between(submission_date, planned_date)
            if pathway == "notification" and lead_days < NOTIFICATION_MIN_WORKING_DAYS:
                errors.append(
                    f"Notification pathway (Điều 9 khoản 4): only {lead_days} working day(s) between "
                    f"submission and the planned date -- at least {NOTIFICATION_MIN_WORKING_DAYS} required"
                )
            if pathway == "approval" and lead_days < APPROVAL_MIN_WORKING_DAYS:
                errors.append(
                    f"Approval pathway (Điều 10 khoản 4a): only {lead_days} working day(s) between "
                    f"submission and the planned date -- at least {APPROVAL_MIN_WORKING_DAYS} required"
                )

    if pathway == "approval":
        entity_type = event.get("organizer_entity_type")
        if entity_type not in ENTITY_TYPES:
            errors.append(
                f"event.organizer_entity_type must be one of {sorted(ENTITY_TYPES)} for the approval "
                f"pathway (Điều 10 khoản 1a eligibility), got {entity_type!r}"
            )
        if event.get("security_order_compliance_declared") is not True:
            errors.append(
                "event.security_order_compliance_declared must be true -- Điều 10 khoản 1b requires meeting "
                "security/public-order conditions (this script cannot verify the substance, only that it "
                "was declared)"
            )
        if event.get("fire_safety_compliance_declared") is not True:
            errors.append(
                "event.fire_safety_compliance_declared must be true -- Điều 10 khoản 1b requires meeting "
                "fire-safety (PCCC) conditions (this script cannot verify the substance, only that it was "
                "declared)"
            )

    return errors, submission_date, planned_date, pathway


def validate_approval_response(resp: object, submission_date: date | None, pathway: str | None) -> list[str]:
    if resp is None:
        return []
    errors: list[str] = []
    if not isinstance(resp, dict):
        return ["approval_response must be an object if present"]
    if pathway != "approval":
        errors.append("approval_response was given but event.pathway is not 'approval' -- the notification pathway has no approval-response step")
        return errors

    if resp.get("application_complete_at_submission") is not True:
        return errors  # incomplete-application timeline (Dieu 10 khoan 4b) not checked here

    response_date_raw = resp.get("response_date")
    try:
        response_date = parse_iso_date(response_date_raw, "approval_response.response_date")
    except RecordError as exc:
        return errors + [str(exc)]

    if submission_date is not None:
        elapsed = working_days_between(submission_date, response_date)
        if elapsed > APPROVAL_RESPONSE_MAX_WORKING_DAYS:
            errors.append(
                f"approval_response: {elapsed} working day(s) elapsed between submission and response -- "
                f"Điều 10 khoản 4c requires the authority respond within {APPROVAL_RESPONSE_MAX_WORKING_DAYS} "
                "working days of a complete application"
            )

    response_type = resp.get("response_type")
    if response_type not in ("approved", "rejected", "pending"):
        errors.append(f"approval_response.response_type must be one of 'approved'/'rejected'/'pending', got {response_type!r}")

    return errors


def validate_changes(changes: object) -> list[str]:
    if changes is None:
        return []
    errors: list[str] = []
    if not isinstance(changes, dict):
        return ["changes must be an object if present"]

    if changes.get("content_changed") is True:
        notice_raw = changes.get("content_change_notice_date")
        if not isinstance(notice_raw, str) or not notice_raw.strip():
            errors.append("changes.content_change_notice_date is required when content_changed is true")

    if changes.get("time_or_location_changed") is True:
        notice_raw = changes.get("time_location_change_notice_date")
        new_date_raw = changes.get("new_planned_date")
        try:
            notice_date = parse_iso_date(notice_raw, "changes.time_location_change_notice_date")
            new_date = parse_iso_date(new_date_raw, "changes.new_planned_date")
            lead = working_days_between(notice_date, new_date)
            if lead < CHANGE_NOTICE_MIN_WORKING_DAYS:
                errors.append(
                    f"changes: only {lead} working day(s) notice before the new planned date -- Điều 10 khoản "
                    f"4đ requires at least {CHANGE_NOTICE_MIN_WORKING_DAYS} working days notice for a time/"
                    "location change to an already-approved event"
                )
        except RecordError as exc:
            errors.append(str(exc))

    return errors


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    if "event" not in record:
        return ["event key is required"]

    event = record.get("event")
    if not isinstance(event, dict):
        return ["event must be an object"]

    event_errors, submission_date, planned_date, pathway = validate_event(event)
    errors.extend(event_errors)
    errors.extend(validate_approval_response(record.get("approval_response"), submission_date, pathway))
    errors.extend(validate_changes(record.get("changes")))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to an event-record JSON file (see assets/event_record_template.json)")
    args = parser.parse_args()

    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict) or "event" not in data:
        print("MALFORMED: input must be a JSON object with at least an 'event' key", file=sys.stderr)
        return 2

    print(
        "NOTE: this checks Nghị định 144/2020/NĐ-CP's notification pathway (Điều 8/9) or approval pathway "
        "(Điều 8/10) lead-time and eligibility rules mechanically. It does NOT verify the substance of "
        "security/fire-safety compliance, does NOT constitute legal advice, and working-day counts exclude "
        "weekends only -- Vietnamese public holidays are not accounted for.",
        file=sys.stderr,
    )

    errors = validate(data)

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK: no flagged issues against Nghị định 144/2020/NĐ-CP's checkable rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
