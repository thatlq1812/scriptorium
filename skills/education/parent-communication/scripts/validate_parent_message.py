#!/usr/bin/env python3
"""Validate a parent-communication message JSON record (a homeroom teacher's
letter or periodic brief to parents) for completeness and tone before it goes
out. Stdlib only (json, re), local, deterministic -- no AI/network of any
kind. This does NOT judge whether the message is well-written; it catches
the boring, embarrassing failure modes: missing required fields, a leftover
template placeholder (most dangerously an unfilled student name on a
single-student letter), a vague "requested_action" that gives the parent
nothing to act on, and harsh/accusatory language about the student that has
no place in a message home.

Checks:
  - Required non-empty fields: purpose, body_sections (>=1 non-empty item),
    sender_name.
  - Unresolved template placeholders anywhere in the record (<TODO>,
    {{...}}, TBD, XXX, bare <...> tokens) -- errors.
  - If recipient_scope == "single_student": student_name_or_placeholder must
    be filled in with a real name, not left as a template placeholder --
    the classic "form letter sent with <student_name> never replaced"
    mistake.
  - If requested_action is stated (non-empty), it must be concrete: not a
    placeholder, not just whitespace.
  - Harsh/accusatory language about the student (hand-curated lexicon) --
    warning, not a hard error, since tone judgment is inherently soft.

Exit codes: 0 = no errors (warnings may still print), 1 = at least one
error, 2 = file not readable / malformed JSON.

Usage:
    python validate_parent_message.py message.json
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

VALID_MESSAGE_TYPES = {"letter", "periodic_brief"}
VALID_RECIPIENT_SCOPES = {"single_student", "whole_class"}

REQUIRED_STRING_FIELDS = ("purpose", "sender_name")

# Same shape as peer-review's PLACEHOLDER_RE: catches <TODO>, [TODO],
# {{jinja}}, TBD, XXX, and bare <...> tokens (URLs/emails in angle brackets
# excluded so a contact_info value like "<gvcn@truong.edu.vn>" isn't a false
# positive -- though contact_info should not normally be angle-bracketed).
PLACEHOLDER_RE = re.compile(
    r"<TODO>|\[TODO\]|\{\{[^}]*\}\}|\bTBD\b|\bXXX\b|<(?![a-zA-Z][a-zA-Z0-9+.-]*://)[^<>@]{1,300}>",
    re.IGNORECASE | re.DOTALL,
)

# Hand-curated: terms inappropriate in a message home about a student --
# harsh, accusatory, or character-judging rather than descriptive of an
# event/behavior. Word-boundary matched to avoid over-triggering on
# unrelated text. Deliberately scoped to this context, not a general
# profanity filter.
ACCUSATORY_RE = re.compile(
    r"\b(hư hỏng|hỗn láo|vô lễ|ngu dốt|đần độn|mất dạy|láo toét|ngổ ngáo|"
    r"bất trị|vô phương cứu chữa|không thể dạy được|vô tích sự|vô ý thức|"
    r"đồ (ngu|dốt|hư)|con hư|stupid|idiotic|hopeless|uncontrollable|"
    r"worthless|useless|good[- ]for[- ]nothing)\b",
    re.I,
)
# Character-judging framing rather than describing a specific event.
PERSONAL_JUDGMENT_RE = re.compile(
    r"\bcon (của )?(anh|chị|ông|bà) (không|chẳng) (ra gì|dạy được|nên người)\b"
    r"|\bkhông (có tương lai|thể sửa được)\b"
    r"|\b(is|are) a (bad|terrible) (kid|student|child)\b",
    re.I,
)


class MessageError(Exception):
    pass


def _is_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_RE.search(value))


def _scan_tone(label: str, text: str, warnings: list[str]) -> None:
    for m in ACCUSATORY_RE.finditer(text):
        warnings.append(f"{label}: harsh/accusatory language about the student ({m.group(0)!r}) -- rephrase to describe the event, not judge the student")
    for m in PERSONAL_JUDGMENT_RE.finditer(text):
        warnings.append(f"{label}: character-judging framing ({m.group(0)!r}) -- describe the specific event/behavior instead")


def validate(msg: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("message_type", "recipient_scope", "purpose", "student_name_or_placeholder",
                  "body_sections", "requested_action", "sender_name", "sender_title", "contact_info"):
        if field not in msg:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, warnings

    message_type = msg["message_type"]
    if message_type not in VALID_MESSAGE_TYPES:
        errors.append(f"message_type must be one of {sorted(VALID_MESSAGE_TYPES)}, got {message_type!r}")

    recipient_scope = msg["recipient_scope"]
    if recipient_scope not in VALID_RECIPIENT_SCOPES:
        errors.append(f"recipient_scope must be one of {sorted(VALID_RECIPIENT_SCOPES)}, got {recipient_scope!r}")

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

    # requested_action: optional (pure FYI messages leave it empty), but if
    # stated it must be concrete -- not whitespace, not a placeholder.
    requested_action = msg.get("requested_action", "")
    if isinstance(requested_action, str) and requested_action.strip():
        if _is_placeholder(requested_action):
            errors.append(f"requested_action is a leftover template placeholder: {requested_action!r}")
    elif not isinstance(requested_action, str):
        errors.append(f"requested_action must be a string (use \"\" for a pure FYI message), got {type(requested_action).__name__}")

    # single_student scope: the real embarrassing-mistake check -- a form
    # letter sent with the student-name placeholder never replaced.
    if recipient_scope == "single_student":
        student_name = msg.get("student_name_or_placeholder", "")
        if not isinstance(student_name, str) or not student_name.strip():
            errors.append("recipient_scope is 'single_student' but student_name_or_placeholder is empty -- fill in the actual student name")
        elif _is_placeholder(student_name):
            errors.append(f"recipient_scope is 'single_student' but student_name_or_placeholder is still a template placeholder: {student_name!r} -- fill in the actual student name before sending")

    # Placeholder scan across every string field (whole-record safety net,
    # catches placeholders in purpose/body_sections/sender_name/etc. too).
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

    for field in ("purpose", "body_sections", "sender_name", "sender_title"):
        if field in msg:
            _walk(msg[field], field)
    # requested_action and student_name_or_placeholder already checked above
    # with their own tailored messages -- skip re-flagging via the generic walk.

    # Tone scan: purpose, body_sections, requested_action are where a
    # teacher describes the student's situation.
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
    parser.add_argument("message", type=Path, help="Path to a parent-message JSON file (see assets/parent_message_template.json)")
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

    print("VALID: required fields present, no leftover placeholders. This confirms completeness and tone only, not message quality -- read any warnings above, they're not blocking but worth acting on.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
