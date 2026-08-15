#!/usr/bin/env python3
"""Check that a clinical intake record and SOAP-format session notes are
STRUCTURALLY complete -- every required section is present and non-empty,
informed consent and confidentiality-handling are declared on file. Stdlib
only (json, argparse, datetime), local, deterministic -- no AI/network
call of any kind.

====================================================================
DOES NOT DIAGNOSE. DOES NOT REPLACE A LICENSED CLINICIAN.
====================================================================
This script NEVER reads, evaluates, or judges the CONTENT of a Subjective/
Objective/Assessment/Plan field -- it checks only that each field is
present and non-empty, exactly the way a front-desk completeness check
would, never the way a clinical supervisor would. It does not assess risk,
does not flag clinical concerns, does not suggest a diagnosis, and does
not evaluate whether a treatment plan is appropriate. This is the single
most important scope limit of any skill in this registry -- built this
way deliberately, following the same explicit boundary a real, independently-
built precedent (chengzhi43/ClarityGuide-skill) already draws for itself:
"does not diagnose, does not replace a therapist."

Grounded in public sources (a real deployed clinical-documentation
product's own SOAP-format documentation, and the APA's own official
Ethics Code), NOT real practitioner elicitation -- see
references/research_16_clinical_note_structure/research_brief.json's own
gaps note. Treat this as a structural-completeness aid only.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python validate_clinical_notes.py <record.json>
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

SOAP_FIELDS = ("subjective", "objective", "assessment", "plan")


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
        errors.append(f"{field} is required and must be non-empty text (presence check only -- content is never read or judged)")


def validate_intake(intake: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(intake, dict):
        return ["intake_record must be an object"]

    if intake.get("completed") is not True:
        errors.append("intake_record.completed must be true before any session note references this client")
    if intake.get("informed_consent_on_file") is not True:
        errors.append(
            "intake_record.informed_consent_on_file must be true -- APA Ethics Code requires informed "
            "consent be obtained and on file before treatment begins"
        )
    if intake.get("confidentiality_handling_declared") is not True:
        errors.append(
            "intake_record.confidentiality_handling_declared must be true -- APA Ethics Code Standard 6.02 "
            "requires a declared plan for protecting record confidentiality across its full lifecycle"
        )

    return errors


def validate_session_note(note: dict, index: int) -> list[str]:
    errors: list[str] = []
    p = f"session_notes[{index}]"

    try:
        parse_iso_date(note.get("session_date"), f"{p}.session_date")
    except RecordError as exc:
        errors.append(str(exc))

    for field in SOAP_FIELDS:
        require_nonempty_text(note.get(field), f"{p}.{field}", errors)

    return errors


def validate(record: dict) -> list[str]:
    errors: list[str] = []

    session_notes = record.get("session_notes")
    has_sessions = isinstance(session_notes, list) and len(session_notes) > 0

    if has_sessions:
        if "intake_record" not in record:
            errors.append("intake_record key is required whenever session_notes is non-empty -- a session note cannot exist without a completed intake")
        else:
            errors.extend(validate_intake(record.get("intake_record")))

    if "session_notes" not in record:
        errors.append("session_notes key is required (use [] if there are none yet)")
    elif not isinstance(session_notes, list):
        errors.append("session_notes must be a list")
    else:
        for i, note in enumerate(session_notes):
            if not isinstance(note, dict):
                errors.append(f"session_notes[{i}] must be an object")
                continue
            errors.extend(validate_session_note(note, i))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("record", type=Path, help="Path to a clinical-note-structure JSON file (see assets/clinical_note_template.json)")
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
        "NOTE: this checks STRUCTURAL COMPLETENESS only (are the intake/consent/confidentiality fields "
        "present, are SOAP sections non-empty) -- it DOES NOT DIAGNOSE, DOES NOT EVALUATE CLINICAL CONTENT, "
        "and DOES NOT REPLACE A LICENSED CLINICIAN. See the script's own module docstring for the full scope "
        "boundary.",
        file=sys.stderr,
    )

    errors = validate(data)

    if errors:
        print(f"FLAGGED: {len(errors)} issue(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    n = len(data.get("session_notes", []) or [])
    print(f"OK: {n} session note(s), structurally complete, no issues found. (Structure only -- not a clinical-quality assessment.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
