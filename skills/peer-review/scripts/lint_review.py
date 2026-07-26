#!/usr/bin/env python3
"""Lint a private review draft Markdown file for: channel separation
("Comments to Authors" vs "Confidential Comments to Editor" as distinct
sections), editor-only content leaking into the authors' channel, unresolved
placeholders, unprofessional tone, and role/decision-overreach phrases (a
reviewer recommends, an editor decides). Stdlib only (re), local,
deterministic. Emits line numbers and rule IDs — never echoes back review
text as a "finding," to keep this report safe to share even though the draft
itself is confidential.

Headings are matched at any level and case-insensitively, so a draft that
writes "### Comments to authors" is not reported as missing the section.

Exit codes: 0 = no flags, 1 = at least one flag found, 2 = file not readable.

Usage:
    python lint_review.py private-review.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

HEADING_RE = re.compile(r"^(#{1,6})\s*(.+?)\s*$")

REQUIRED_SECTIONS = {
    "comments-to-authors": (re.compile(r"^comments?\s+to\s+(the\s+)?authors?\b[\s:.-]*$", re.I),
                            "Comments to Authors"),
    "confidential-comments-to-editor": (re.compile(r"^(confidential\s+)?comments?\s+to\s+(the\s+)?editor\b[\s:.-]*$", re.I),
                                        "Confidential Comments to Editor"),
}

# Scanned over the whole text (not line by line) so multi-line instructional
# placeholders like "<For each: ...\n...>" are caught too. URLs/emails in
# angle brackets are excluded; HTML comments are masked out beforehand.
PLACEHOLDER_RE = re.compile(
    r"<TODO>|\[TODO\]|\{\{[^}]*\}\}|\bTBD\b|\bXXX\b|<(?![a-zA-Z][a-zA-Z0-9+.-]*://)[^<>@]{1,300}>",
    re.IGNORECASE | re.DOTALL,
)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

# Word-boundary matched, and deliberately limited to terms that are
# unprofessional in any context — "garbage collection" and "lazy evaluation"
# are legitimate technical terms and must not be flagged as abuse.
ABUSIVE_RE = re.compile(
    r"\b(stupid|idiotic|idiots?|incompetent|clueless|worthless|amateurish|pathetic|garbage|rubbish|trash)\b"
    r"(?!\s+(collection|collector|collected))",
    re.I,
)
# Attacks on the people rather than the work.
PERSONAL_ATTACK_RE = re.compile(
    r"\bthe authors? (clearly |obviously |evidently )?(do(es)? not|don'?t|doesn'?t) understand\b"
    r"|\bthe authors? (are|is) not (qualified|competent)\b"
    r"|\bwhoever wrote this\b"
    r"|\bthe authors? should not be (publishing|writing|doing)\b",
    re.I,
)
# A reviewer recommends; only language that ANNOUNCES the outcome is overreach.
DECISION_OVERREACH_RE = re.compile(
    r"\b(I|we) (hereby )?(reject|accept) this (manuscript|paper|submission)\b"
    r"|\b(I am|we are) (rejecting|accepting) this (manuscript|paper|submission)\b"
    r"|\bthis (manuscript|paper|submission) (is|has been|will be) (hereby )?(rejected|accepted)\b"
    r"|\b(editorial|final) decision\s*:"
    r"|\bthe decision (is|will be) (rejection|acceptance|to reject|to accept)\b",
    re.I,
)
# Content that belongs in the editor channel, found in the authors' channel.
EDITOR_ONLY_IN_AUTHOR_CHANNEL = [
    (re.compile(r"\bdear editor\b", re.I), "addressed to the editor"),
    (re.compile(r"\bconfidential\b", re.I), "marked confidential"),
    (re.compile(r"\b(conflict|competing) of? ?interests?\b", re.I), "conflict-of-interest disclosure"),
    (re.compile(r"\b(plagiaris(m|ed|ing)|research misconduct|data fabrication|fabricated data)\b", re.I),
     "integrity allegation"),
    (re.compile(r"\b(I|we) recommend (rejection|acceptance|to reject|to accept)\b", re.I),
     "recommendation to the editor"),
]


def split_sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Map each required section key to its (start_line, end_line), 1-indexed.

    A section ends at the next heading of the same or a higher level.
    """
    headings: list[tuple[int, int, str]] = []
    in_fence = False
    for lineno, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if match:
            headings.append((lineno, len(match.group(1)), match.group(2)))

    found: dict[str, tuple[int, int]] = {}
    for index, (lineno, level, title) in enumerate(headings):
        for key, (pattern, _label) in REQUIRED_SECTIONS.items():
            if key in found or not pattern.match(title):
                continue
            end = len(lines)
            for next_lineno, next_level, _ in headings[index + 1:]:
                if next_level <= level:
                    end = next_lineno - 1
                    break
            found[key] = (lineno, end)
    return found


def _mask_comments(text: str) -> str:
    """Blank out HTML comments while preserving line numbering."""
    return HTML_COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def _summarize_placeholder(matched: str) -> str:
    """Report the shape of a placeholder, never a whole block of review text."""
    single_line = re.sub(r"\s+", " ", matched).strip()
    return single_line if len(single_line) <= 40 else single_line[:37] + "...>"


def lint(text: str) -> tuple[list[str], list[dict]]:
    lines = text.splitlines()
    sections = split_sections(lines)

    section_errors = [
        f"missing required section heading: {label!r} (channel separation)"
        for key, (_pattern, label) in REQUIRED_SECTIONS.items() if key not in sections
    ]

    flags: list[dict] = []
    masked = _mask_comments(text)
    for m in PLACEHOLDER_RE.finditer(masked):
        flags.append({
            "line": masked.count("\n", 0, m.start()) + 1,
            "rule": "unresolved-placeholder",
            "matched": _summarize_placeholder(m.group(0)),
        })

    for lineno, line in enumerate(lines, start=1):
        for m in ABUSIVE_RE.finditer(line):
            flags.append({"line": lineno, "rule": "abusive-language", "matched": m.group(0)})
        for m in PERSONAL_ATTACK_RE.finditer(line):
            flags.append({"line": lineno, "rule": "personal-attack", "matched": m.group(0)})
        for m in DECISION_OVERREACH_RE.finditer(line):
            flags.append({"line": lineno, "rule": "decision-overreach", "matched": m.group(0)})

    author_range = sections.get("comments-to-authors")
    if author_range:
        start, end = author_range
        for lineno in range(start, min(end, len(lines)) + 1):
            for pattern, label in EDITOR_ONLY_IN_AUTHOR_CHANNEL:
                if pattern.search(lines[lineno - 1]):
                    flags.append({"line": lineno, "rule": "channel-leak", "matched": f"{label} inside Comments to Authors"})
    return section_errors, flags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("review", type=Path, help="Private review draft to lint")
    args = parser.parse_args()

    if not args.review.is_file():
        print(f"FILE NOT FOUND: {args.review}", file=sys.stderr)
        return 2
    try:
        text = args.review.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"CANNOT READ: {exc}", file=sys.stderr)
        return 2

    section_errors, flags = lint(text)

    total = len(section_errors) + len(flags)
    if total == 0:
        print("OK: channel separation present, no placeholders/abusive-language/decision-overreach patterns matched.")
        print("This is a lint, not a substitute for the accountable human's own read-through.")
        return 0

    print(f"FLAGGED: {total} issue(s).")
    for e in section_errors:
        print(f"  [structure] {e}")
    for f in sorted(flags, key=lambda f: f["line"]):
        print(f"  line {f['line']} [{f['rule']}] '{f['matched']}'")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
