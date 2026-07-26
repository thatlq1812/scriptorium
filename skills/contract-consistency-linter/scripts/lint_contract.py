#!/usr/bin/env python3
"""Lint a Vietnamese contract text for mechanical consistency errors —
article (Điều) numbering, cross-reference integrity, and party-label
consistency. Stdlib only (re, json, argparse), local, deterministic, no
AI/LLM call of any kind.

This checks the three purely mechanical failure modes named directly in
the legal-practitioner survey this skill was elicited from ("kiểm tra
chính tả và định dạng... cách đánh số điều khoản", "kiểm tra tính nhất
quán... tên các bên... điều khoản tham chiếu"). It does NOT assess legal
risk, clause fairness, or compliance — that is `contract-risk-log`'s job,
and stays a human/agent judgment call.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = malformed input.

Usage:
    python lint_contract.py <contract.txt> <config.json>
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

ARTICLE_HEADING_RE = re.compile(r"^\s*Điều\s+(\d+)\b")
ARTICLE_MENTION_RE = re.compile(r"\bĐiều\s+(\d+)\b")
PARTY_MENTION_RE = re.compile(r"\bBên\s+([A-ZĐ]\S*)", re.UNICODE)


class LintError(Exception):
    pass


def load_config(path: Path) -> dict:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LintError(f"cannot read config: {exc}") from exc
    if not isinstance(config, dict) or not config.get("allowed_party_labels"):
        raise LintError("config.json must have a non-empty 'allowed_party_labels' list")
    labels = config["allowed_party_labels"]
    if not isinstance(labels, list) or not all(isinstance(l, str) and l.strip() for l in labels):
        raise LintError("'allowed_party_labels' must be a list of non-empty strings")
    return config


def find_article_headings(lines: list[str]) -> list[tuple[int, int]]:
    """Returns [(line_number, article_number), ...] in document order."""
    headings = []
    for lineno, line in enumerate(lines, start=1):
        m = ARTICLE_HEADING_RE.match(line)
        if m:
            headings.append((lineno, int(m.group(1))))
    return headings


def check_numbering(headings: list[tuple[int, int]]) -> list[str]:
    errors = []
    seen: dict[int, int] = {}
    expected = 1
    for lineno, number in headings:
        if number in seen:
            errors.append(f"line {lineno}: duplicate 'Điều {number}' (first declared at line {seen[number]})")
            continue
        seen[number] = lineno
        if number != expected:
            errors.append(f"line {lineno}: 'Điều {number}' is out of sequence (expected 'Điều {expected}')")
        expected = number + 1
    return errors


def check_cross_references(lines: list[str], headings: list[tuple[int, int]]) -> list[str]:
    declared = {number for _lineno, number in headings}
    heading_lines = {lineno for lineno, _number in headings}
    errors = []
    for lineno, line in enumerate(lines, start=1):
        if lineno in heading_lines:
            continue
        for m in ARTICLE_MENTION_RE.finditer(line):
            number = int(m.group(1))
            if number not in declared:
                errors.append(f"line {lineno}: reference to 'Điều {number}' has no matching heading anywhere in the document (dangling cross-reference)")
    return errors


def check_party_labels(lines: list[str], allowed_labels: list[str]) -> list[str]:
    allowed_second_words = set()
    for label in allowed_labels:
        parts = label.strip().split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bên":
            allowed_second_words.add(parts[1])
    errors = []
    for lineno, line in enumerate(lines, start=1):
        for m in PARTY_MENTION_RE.finditer(line):
            word = m.group(1).rstrip(".,:;)")
            if word not in allowed_second_words:
                errors.append(f"line {lineno}: 'Bên {word}' is not in the declared party labels {sorted(allowed_second_words)} -- likely a leftover/copy-paste error")
    return errors


def lint(text: str, config: dict) -> list[str]:
    lines = text.splitlines()
    headings = find_article_headings(lines)
    errors: list[str] = []
    errors.extend(check_numbering(headings))
    errors.extend(check_cross_references(lines, headings))
    errors.extend(check_party_labels(lines, config["allowed_party_labels"]))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("contract", type=Path, help="Plain text/Markdown contract file (UTF-8)")
    parser.add_argument("config", type=Path, help="Path to a config JSON (see assets/lint_config_template.json)")
    args = parser.parse_args()

    if not args.contract.is_file():
        print(f"MALFORMED: contract file not found: {args.contract}", file=sys.stderr)
        return 2

    try:
        config = load_config(args.config)
    except LintError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    try:
        text = args.contract.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"MALFORMED: cannot read contract as UTF-8 text: {exc}", file=sys.stderr)
        return 2

    errors = lint(text, config)

    if not errors:
        print("OK: no numbering/cross-reference/party-label inconsistencies found. This is a mechanical lint, not a legal review.")
        return 0

    print(f"FLAGGED: {len(errors)} issue(s).")
    for e in errors:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
