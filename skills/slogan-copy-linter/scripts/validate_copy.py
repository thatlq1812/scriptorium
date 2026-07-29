#!/usr/bin/env python3
"""Structure/tone linter for short marketing copy (slogans, taglines).

Deterministic checks only: length cap (caller-declared, since the right
cap depends on the physical medium -- a signboard slogan and a banner
tagline have different real-estate constraints, never guessed here),
banned-word substring scan (caller-declared list), and an all-caps
"shouting" warning (non-blocking, since some brands intentionally use
all-caps -- caller can declare allow_all_caps to suppress it).

Usage:
    python validate_copy.py <copy.json>

Exit 0 = valid (warnings may still print), 1 = hard violations (all printed), 2 = malformed input.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_copy.py <copy.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed JSON in {path}: {e}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("ERROR: copy.json must be a JSON object.", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []

    slogan = data.get("slogan")
    if not isinstance(slogan, str) or not slogan.strip():
        errors.append("'slogan' must be a non-empty string")
        slogan = ""

    max_chars = data.get("max_chars")
    if not isinstance(max_chars, int) or max_chars <= 0:
        errors.append("'max_chars' must be a positive integer (caller-declared, no built-in default)")
    elif slogan and len(slogan) > max_chars:
        errors.append(f"slogan is {len(slogan)} chars, exceeds declared max_chars={max_chars}")

    banned_words = data.get("banned_words", [])
    if not isinstance(banned_words, list):
        errors.append("'banned_words' must be a list if present")
        banned_words = []

    if slogan:
        slogan_lower = slogan.lower()
        for word in banned_words:
            if isinstance(word, str) and word.lower() in slogan_lower:
                errors.append(f"slogan contains banned word/phrase: '{word}'")

        letters = [c for c in slogan if c.isalpha()]
        if letters and all(c.isupper() for c in letters) and not data.get("allow_all_caps", False):
            warnings.append("slogan is entirely uppercase ('shouting') -- set allow_all_caps: true if this is intentional brand style")

    if errors:
        print(f"INVALID ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    if warnings:
        print(f"VALID with {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - {w}")
    else:
        print(f"VALID: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
