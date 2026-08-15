#!/usr/bin/env python3
"""Check FORMAT/PROTOCOL of diplomatic material against 2 real, stable
conventions -- a note verbale's required structural shape (third-person
voice, letterhead/date/reference, fixed opening/closing formula), and
diplomatic-mission precedence ordering per the Vienna Convention on
Diplomatic Relations (1961) -- ranked by precedence class, then by date/
time of credential presentation within each class. Stdlib only (json,
argparse, re, datetime), local, deterministic -- no AI/network call.

CRITICAL SCOPE LIMIT (read before use): this checks FORMAT/PROTOCOL only.
It does NOT and CANNOT judge the actual diplomatic/policy content of a
note verbale, does NOT verify precedence-class assignment itself (only
that a caller-declared class+date ordering is internally consistent), and
is NOT a substitute for a real protocol officer's judgment on a specific,
consequential diplomatic matter.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_diplomatic_correspondence.py <record.json>
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

FIRST_PERSON_RE = re.compile(r"\b(I|we|our|us|my|me)\b", re.IGNORECASE)
OPENING_HINT_RE = re.compile(r"presents? its compliments", re.IGNORECASE)
CLOSING_HINT_RE = re.compile(r"avails? itself|highest consideration", re.IGNORECASE)


class RecordError(Exception):
    pass


def require_nonempty_text(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required and must be non-empty text")


def parse_iso_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise RecordError(f"{field} must be an ISO date string 'YYYY-MM-DD', got {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RecordError(f"{field} is not a real calendar date: {value!r} ({exc})") from exc


def validate_note_verbale(note: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(note, dict):
        return ["note_verbale must be an object"]

    require_nonempty_text(note.get("sending_office"), "note_verbale.sending_office", errors)
    require_nonempty_text(note.get("recipient_office"), "note_verbale.recipient_office", errors)
    require_nonempty_text(note.get("reference_number"), "note_verbale.reference_number", errors)
    try:
        parse_iso_date(note.get("date"), "note_verbale.date")
    except RecordError as exc:
        errors.append(str(exc))

    body = note.get("body")
    if not isinstance(body, str) or not body.strip():
        errors.append("note_verbale.body is required and must be non-empty text")
        return errors

    if not OPENING_HINT_RE.search(body):
        errors.append(
            "note_verbale.body does not contain a recognizable opening compliments formula "
            "(e.g. 'presents its compliments to ... and has the honor to') -- a note verbale is "
            "expected to open with a fixed formal salutation, not begin directly with the matter"
        )
    if not CLOSING_HINT_RE.search(body):
        errors.append(
            "note_verbale.body does not contain a recognizable closing formula (e.g. 'avails itself of "
            "this opportunity' / 'assurances of its highest consideration') -- a note verbale is expected "
            "to close with a fixed formal valediction"
        )

    first_person_hits = sorted(set(m.group(0).lower() for m in FIRST_PERSON_RE.finditer(body)))
    if first_person_hits:
        errors.append(
            f"note_verbale.body uses first-person language ({first_person_hits}) -- a note verbale is "
            "written in the THIRD PERSON throughout ('the Embassy...', never 'I'/'we')"
        )

    return errors


def validate_precedence_list(missions: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(missions, list) or not missions:
        return ["precedence_list must be a non-empty list"]

    parsed: list[tuple[int, str, date, int]] = []
    for i, m in enumerate(missions):
        if not isinstance(m, dict):
            errors.append(f"precedence_list[{i}] must be an object")
            continue
        p = f"precedence_list[{i}]"
        require_nonempty_text(m.get("mission_name"), f"{p}.mission_name", errors)

        rank_class = m.get("precedence_class")
        if not isinstance(rank_class, int) or isinstance(rank_class, bool) or rank_class < 1:
            errors.append(f"{p}.precedence_class must be a positive integer (1 = highest class), got {rank_class!r}")
            rank_class = None

        try:
            credential_date = parse_iso_date(m.get("credential_presentation_date"), f"{p}.credential_presentation_date")
        except RecordError as exc:
            errors.append(str(exc))
            credential_date = None

        declared_order = m.get("declared_order")
        if not isinstance(declared_order, int) or isinstance(declared_order, bool) or declared_order < 1:
            errors.append(f"{p}.declared_order must be a positive integer, got {declared_order!r}")
            declared_order = None

        if rank_class is not None and credential_date is not None and declared_order is not None:
            parsed.append((rank_class, m.get("mission_name", f"#{i}"), credential_date, declared_order))

    if len(parsed) == len(missions):
        # Vienna Convention: rank by precedence_class first, then by credential date within class.
        expected_order = sorted(
            range(len(parsed)), key=lambda idx: (parsed[idx][0], parsed[idx][2])
        )
        declared_by_position = sorted(range(len(parsed)), key=lambda idx: parsed[idx][3])
        if expected_order != declared_by_position:
            errors.append(
                "precedence_list.declared_order does not match Vienna Convention ordering (rank by "
                "precedence_class ascending, then by credential_presentation_date ascending within the same "
                "class) -- recompute the declared_order sequence from those 2 fields, not by any other "
                "criterion (e.g. sending state's size/seniority, which the Convention explicitly does not use)"
            )

    return errors


def validate(record: dict) -> list[str]:
    errors: list[str] = []
    if "note_verbale" in record:
        errors.extend(validate_note_verbale(record.get("note_verbale")))
    if "precedence_list" in record:
        errors.extend(validate_precedence_list(record.get("precedence_list")))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to a diplomatic-record JSON file (see assets/diplomatic_record_template.json)")
    args = parser.parse_args()

    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict) or not ("note_verbale" in data or "precedence_list" in data):
        print("MALFORMED: input must be a JSON object with at least one of 'note_verbale' or 'precedence_list'", file=sys.stderr)
        return 2

    print(
        "NOTE: this checks note-verbale FORMAT (third-person voice, opening/closing formula) and "
        "precedence-list ORDERING (Vienna Convention: precedence class, then credential-presentation date) "
        "only -- it cannot and does not judge diplomatic/policy content, and is not a substitute for a real "
        "protocol officer's judgment on a consequential matter.",
        file=sys.stderr,
    )

    errors = validate(data)

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK: no format/protocol issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
