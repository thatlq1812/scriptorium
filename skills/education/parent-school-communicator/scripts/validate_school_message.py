#!/usr/bin/env python3
"""Validate a parent-to-school message JSON record (a parent/guardian
writing to a teacher or school -- meeting request, concern, follow-up,
inquiry, absence notice, complaint) for completeness and tone before it
goes out. Stdlib only (json, re), local, deterministic -- no AI/network of
any kind. This does NOT judge whether the message is well-written; it
catches the boring, embarrassing failure modes: missing required fields, a
leftover template placeholder, a vague/missing concrete ask (this is the
opposite direction of parent-communication's FYI-allowed rule -- a parent
contacting a school is assumed to want something to happen next), and
hostile/threatening language toward the teacher/school that would derail
the message before it's even read.

Checks:
  - Required non-empty fields: recipient_name, sender_name, student_name,
    purpose, body_sections (>=1 non-empty item), requested_action.
  - Unresolved template placeholders anywhere in the record (<TODO>,
    {{...}}, TBD, XXX, bare <...> tokens) -- errors.
  - requested_action must always be concrete and non-empty for this
    direction of communication -- unlike parent-communication's
    teacher-to-parent letters (where a pure-FYI empty ask is valid), a
    parent contacting a school is assumed to always want a specific next
    step, even if that step is only "please confirm receipt."
  - Hostile/threatening language toward the teacher/school (hand-curated
    lexicon) -- warning, not a hard error, since tone judgment is
    inherently soft and a parent may have a legitimate grievance to raise
    firmly without it being disqualifying.

Exit codes: 0 = no errors (warnings may still print), 1 = at least one
error, 2 = file not readable / malformed JSON.

Usage:
    python validate_school_message.py message.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_COMMUNICATION_TYPES = {
    "meeting_request", "concern", "follow_up", "inquiry", "absence_notice", "complaint",
}

REQUIRED_STRING_FIELDS = ("recipient_name", "sender_name", "student_name", "purpose", "requested_action")

# Same shape as parent-communication's PLACEHOLDER_RE: catches <TODO>,
# [TODO], {{jinja}}, TBD, XXX, and bare <...> tokens (URLs/emails in angle
# brackets excluded so contact_info like "<phu.huynh@email.com>" isn't a
# false positive).
PLACEHOLDER_RE = re.compile(
    r"<TODO>|\[TODO\]|\{\{[^}]*\}\}|\bTBD\b|\bXXX\b|<(?![a-zA-Z][a-zA-Z0-9+.-]*://)[^<>@]{1,300}>",
    re.IGNORECASE | re.DOTALL,
)

# Hand-curated: terms that read as a hostile/threatening escalation toward
# a teacher or school, rather than a firm-but-constructive concern. This is
# the mirror-image lexicon of parent-communication's ACCUSATORY_RE/
# PERSONAL_JUDGMENT_RE (which flags harshness ABOUT a student) -- here the
# target is the teacher/school being addressed. Deliberately scoped to this
# context, not a general profanity/legal-threat filter, and deliberately a
# warning, not a block: a parent may have real grounds to be firm.
HOSTILE_RE = re.compile(
    r"\b(vo trach nhiem|vo nang luc|thieu chuyen nghiep|coi thuong|ap dat|"
    r"toi se kien|toi se bao cong an|toi se to cao|se to cao nha truong|"
    r"khong xung dang (lam|day)|day do gi|vo y thuc|"
    r"incompetent|unprofessional|negligent|i will sue|lawsuit|"
    r"file a complaint with the (police|media)|you people|"
    r"disgraceful|shameful|outrageous|unacceptable behavior on your part)\b",
    re.I,
)
THREAT_RE = re.compile(
    r"\b(neu khong|neu khong duoc|nếu không).{0,40}(toi se|se) (kien|kiện|to cao|bao cong an|"
    r"báo (len|lên)|khieu nai|khiếu nại)\b"
    r"|\bif (you|this) (don't|doesn't|do not|does not).{0,40}\b(i will|we will|i'll|we'll)\b",
    re.I,
)


class MessageError(Exception):
    pass


def _is_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_RE.search(value))


def _scan_tone(label: str, text: str, warnings: list[str]) -> None:
    for m in HOSTILE_RE.finditer(text):
        warnings.append(f"{label}: hostile/escalating language toward the teacher/school ({m.group(0)!r}) -- consider a firmer-but-constructive phrasing")
    for m in THREAT_RE.finditer(text):
        warnings.append(f"{label}: reads as a conditional threat ({m.group(0)!r}) -- confirm this is deliberate before sending")


def validate(msg: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("communication_type", "recipient_name", "recipient_role", "sender_name",
                  "student_name", "purpose", "body_sections", "requested_action", "contact_info"):
        if field not in msg:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, warnings

    communication_type = msg["communication_type"]
    if communication_type not in VALID_COMMUNICATION_TYPES:
        errors.append(f"communication_type must be one of {sorted(VALID_COMMUNICATION_TYPES)}, got {communication_type!r}")

    for field in REQUIRED_STRING_FIELDS:
        value = msg.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required and must be a non-empty string")

    body_sections = msg.get("body_sections")
    if not isinstance(body_sections, list) or not body_sections:
        errors.append("body_sections must be a non-empty list")
    else:
        non_empty = [s for s in body_sections if isinstance(s, str) and s.strip()]
        if not non_empty:
            errors.append("body_sections must contain at least 1 non-empty item")
        for i, s in enumerate(body_sections):
            if not isinstance(s, str):
                errors.append(f"body_sections[{i}] must be a string, got {type(s).__name__}")

    # requested_action: unlike parent-communication (teacher->parent, where
    # a pure-FYI empty ask is valid), this direction always requires a
    # concrete ask -- checked above via REQUIRED_STRING_FIELDS for
    # presence/non-empty; here just check it isn't a placeholder.
    requested_action = msg.get("requested_action", "")
    if isinstance(requested_action, str) and requested_action.strip():
        if _is_placeholder(requested_action):
            errors.append(f"requested_action is a leftover template placeholder: {requested_action!r}")

    # recipient_name: the mirror of parent-communication's single-student
    # hard-block -- a message addressed to an unfilled/placeholder
    # recipient is the parent-side equivalent embarrassing mistake (a form
    # letter never addressed to the actual teacher/school contact).
    recipient_name = msg.get("recipient_name", "")
    if isinstance(recipient_name, str) and recipient_name.strip() and _is_placeholder(recipient_name):
        errors.append(f"recipient_name is still a template placeholder: {recipient_name!r} -- fill in the actual teacher/school contact before sending")

    # Placeholder scan across every string field (whole-record safety net).
    def _walk(value, path: str):
        if isinstance(value, str):
            if _is_placeholder(value):
                errors.append(f"{path}: leftover template placeholder: {value!r}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                _walk(item, f"{path}[{i}]")
        elif isinstance(value, dict):
            for key, item in value.items():
                _walk(item, f"{path}.{key}")

    for field in ("purpose", "body_sections", "sender_name", "student_name", "recipient_role"):
        if field in msg:
            _walk(msg[field], field)
    # requested_action and recipient_name already checked above with their
    # own tailored messages -- skip re-flagging via the generic walk.

    # Tone scan: purpose, body_sections, requested_action are where a
    # parent describes the situation and what they want done.
    if isinstance(msg.get("purpose"), str):
        _scan_tone("purpose", msg["purpose"], warnings)
    if isinstance(body_sections, list):
        for i, s in enumerate(body_sections):
            if isinstance(s, str):
                _scan_tone(f"body_sections[{i}]", s, warnings)
    if isinstance(requested_action, str):
        _scan_tone("requested_action", requested_action, warnings)

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("message", type=Path, help="Path to a parent-to-school message JSON file (see assets/school_message_template.json)")
    args = parser.parse_args()

    try:
        msg = json.loads(args.message.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(msg, dict):
        print("MALFORMED: top-level JSON must be an object", file=sys.stderr)
        return 2

    errors, warnings = validate(msg)

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALID: required fields present, concrete ask stated, no leftover placeholders. This confirms completeness and tone only, not message quality -- read any warnings above, they're not blocking but worth acting on.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
