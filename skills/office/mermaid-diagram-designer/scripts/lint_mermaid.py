#!/usr/bin/env python3
"""Structural lint for a Mermaid diagram source — NOT a full parser/renderer
(that needs Node + the mermaid JS engine). Catches common authoring mistakes
before handing the diagram to the user. Stdlib only.

Usage:
    python lint_mermaid.py <diagram.mmd>
    echo '...' | python lint_mermaid.py -
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

KNOWN_KEYWORDS = {
    "flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
    "stateDiagram-v2", "erDiagram", "gantt", "pie", "journey", "mindmap",
    "timeline", "quadrantChart", "gitGraph", "requirementDiagram", "c4Context",
}

BRACKET_PAIRS = {"[": "]", "(": ")", "{": "}"}


def lint(text: str) -> list[str]:
    issues: list[str] = []
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return ["Empty diagram."]

    first_token = lines[0].strip().split()[0] if lines[0].strip() else ""
    if first_token not in KNOWN_KEYWORDS:
        issues.append(
            f"First line '{lines[0].strip()}' doesn't match a known diagram-type keyword "
            f"({', '.join(sorted(KNOWN_KEYWORDS))})."
        )

    # Bracket balance across the whole text (ignore brackets inside quoted labels).
    stack: list[str] = []
    in_quote = False
    for i, ch in enumerate(text):
        if ch == '"':
            in_quote = not in_quote
            continue
        if in_quote:
            continue
        if ch in BRACKET_PAIRS:
            stack.append(BRACKET_PAIRS[ch])
        elif ch in BRACKET_PAIRS.values():
            if not stack or stack.pop() != ch:
                issues.append(f"Bracket '{ch}' at position {i} doesn't match — check the node/label structure.")
    if stack:
        issues.append(f"Missing {len(stack)} closing bracket(s) at the end of the diagram (still open: {stack}).")

    if text.count('"') % 2 != 0:
        issues.append("Odd number of double quotes — a label is unclosed.")

    if "stateDiagram\n" in text or text.strip().startswith("stateDiagram\n"):
        issues.append("Using the old 'stateDiagram' — 'stateDiagram-v2' is recommended for richer syntax.")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Path to a .mmd file, or '-' to read from stdin")
    args = parser.parse_args()

    text = sys.stdin.read() if args.source == "-" else Path(args.source).read_text(encoding="utf-8")
    issues = lint(text)

    if not issues:
        print("OK: no obvious structural errors found (rough lint, not a substitute for a real render to verify).")
        return 0

    print(f"{len(issues)} issue(s):")
    for issue in issues:
        print(f"  - {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
