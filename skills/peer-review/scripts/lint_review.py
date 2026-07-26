#!/usr/bin/env python3
"""Lint a private review draft Markdown file for: channel separation
("Comments to Authors" vs "Confidential Comments to Editor" as distinct
sections), unresolved placeholders, a narrow abusive-language lexicon, and
role/decision-overreach phrases (a reviewer recommends, an editor decides).
Stdlib only (re), local, deterministic. Emits line numbers and rule IDs —
never echoes back full review text as a "finding," to keep this report safe
to share even though the draft itself is confidential.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = file not found.

Usage:
    python lint_review.py private-review.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REQUIRED_SECTIONS = ["## Comments to Authors", "## Confidential Comments to Editor"]

PLACEHOLDER_RE = re.compile(r"<TODO>|<missing>|<[A-Za-z_ ]+>", re.I)

ABUSIVE_LEXICON = [
    "stupid", "idiotic", "idiot", "incompetent", "garbage", "worthless",
    "nonsense", "lazy", "sloppy authors", "clueless",
]

DECISION_OVERREACH_RE = re.compile(
    r"\b(I |we )?(hereby )?(reject|accept) this (manuscript|paper|submission)\b"
    r"|\beditorial decision\s*:"
    r"|\bthis (manuscript|paper) is (rejected|accepted)\b",
    re.I,
)


def lint(text: str) -> tuple[list[str], list[dict]]:
    section_errors = []
    for section in REQUIRED_SECTIONS:
        if section not in text:
            section_errors.append(f"missing required section heading: {section!r} (channel separation)")

    flags: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in PLACEHOLDER_RE.finditer(line):
            flags.append({"line": lineno, "rule": "unresolved-placeholder", "matched": m.group(0)})
        lowered = line.lower()
        for term in ABUSIVE_LEXICON:
            if term in lowered:
                flags.append({"line": lineno, "rule": "abusive-language", "matched": term})
        for m in DECISION_OVERREACH_RE.finditer(line):
            flags.append({"line": lineno, "rule": "decision-overreach", "matched": m.group(0)})

    return section_errors, flags


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python lint_review.py private-review.md", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"FILE NOT FOUND: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    section_errors, flags = lint(text)

    total = len(section_errors) + len(flags)
    if total == 0:
        print("OK: channel separation present, no placeholders/abusive-language/decision-overreach patterns matched.")
        print("This is a lint, not a substitute for the accountable human's own read-through.")
        return 0

    print(f"FLAGGED: {total} issue(s).")
    for e in section_errors:
        print(f"  [structure] {e}")
    for f in flags:
        print(f"  line {f['line']} [{f['rule']}] '{f['matched']}'")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
