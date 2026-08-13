#!/usr/bin/env python3
"""Validate a document-distillation skill's output against the on-demand
reference-scaffolding discipline (master SKILL.md kept small, chapters/
loaded on demand, no dangling cross-references, no leftover placeholders).

Token counts are an APPROXIMATION (word_count * 1.3, a common rough
English-text heuristic) -- this project has no tokenizer dependency and
does not claim exact tokenizer-level precision. Never trust this script's
numbers as exact; they exist to catch a master SKILL.md that has obviously
ballooned past its budget, not to certify a precise count.

Usage:
    python validate_distillation.py <skill_dir>

Exit 0 = valid, 1 = violations found (all printed), 2 = malformed structure.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

TOKENS_PER_WORD = 1.3
SKILL_MD_TOKEN_BUDGET_DEFAULT = 4000
CHAPTER_TOKEN_CEILING_DEFAULT = 3000
CHAPTER_FILE_RE = re.compile(r"^ch(\d{2})-.+\.md$")
CHAPTER_REF_RE = re.compile(r"\bCh\s?(\d{1,2})\b")
PLACEHOLDER_RE = re.compile(r"<[^>\n]{1,80}>")


def _approx_tokens(text: str) -> int:
    words = len(text.split())
    return int(words * TOKENS_PER_WORD)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir")
    parser.add_argument("--skill-md-budget", type=int, default=SKILL_MD_TOKEN_BUDGET_DEFAULT)
    parser.add_argument("--chapter-ceiling", type=int, default=CHAPTER_TOKEN_CEILING_DEFAULT)
    parser.add_argument("--allow-placeholders", action="store_true", help="Skip the leftover-<placeholder> check (use during Analyze-Only/in-progress review)")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    if not skill_dir.exists() or not skill_dir.is_dir():
        print(f"ERROR: not a directory: {skill_dir}", file=sys.stderr)
        return 2

    skill_md = skill_dir / "SKILL.md"
    chapters_dir = skill_dir / "chapters"
    if not skill_md.exists():
        print(f"ERROR: missing {skill_md}", file=sys.stderr)
        return 2
    if not chapters_dir.exists() or not chapters_dir.is_dir():
        print(f"ERROR: missing chapters/ directory at {chapters_dir}", file=sys.stderr)
        return 2

    chapter_files = sorted(chapters_dir.glob("*.md"))
    if not chapter_files:
        print("ERROR: chapters/ directory is empty.", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []

    chapter_numbers: set[int] = set()
    for cf in chapter_files:
        m = CHAPTER_FILE_RE.match(cf.name)
        if not m:
            errors.append(f"chapters/{cf.name}: doesn't match required naming 'chNN-<slug>.md'")
            continue
        chapter_numbers.add(int(m.group(1)))

    for cf in chapter_files:
        text = cf.read_text(encoding="utf-8")
        tokens = _approx_tokens(text)
        if tokens > args.chapter_ceiling:
            errors.append(f"chapters/{cf.name}: ~{tokens} tokens (approx.) exceeds ceiling {args.chapter_ceiling}")
        if not args.allow_placeholders:
            leftover = PLACEHOLDER_RE.findall(text)
            leftover = [p for p in leftover if not p.startswith("<!--")]
            if leftover:
                errors.append(f"chapters/{cf.name}: {len(leftover)} unfilled placeholder(s) remain, e.g. {leftover[0]!r}")

        for ref_match in CHAPTER_REF_RE.finditer(text):
            ref_num = int(ref_match.group(1))
            if ref_num not in chapter_numbers:
                warnings.append(f"chapters/{cf.name}: references 'Ch {ref_num:02d}' which doesn't exist in chapters/ (dangling cross-reference)")

    skill_md_text = skill_md.read_text(encoding="utf-8")
    fm_end = skill_md_text.find("\n---", 4)
    body = skill_md_text[fm_end + 4:] if fm_end != -1 else skill_md_text
    body_tokens = _approx_tokens(body)
    if body_tokens > args.skill_md_budget:
        errors.append(f"SKILL.md body: ~{body_tokens} tokens (approx.) exceeds budget {args.skill_md_budget} -- move detail into chapters/references, loaded on-demand")

    if not args.allow_placeholders:
        body_leftover = [p for p in PLACEHOLDER_RE.findall(body) if not p.startswith("<!--")]
        if body_leftover:
            errors.append(f"SKILL.md: {len(body_leftover)} unfilled placeholder(s) remain, e.g. {body_leftover[0]!r}")

    for supporting in ("glossary.md", "patterns.md", "cheatsheet.md"):
        path = skill_dir / supporting
        if not path.exists():
            errors.append(f"missing supporting file: {supporting}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"{supporting} exists but is empty")

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
        print(f"VALID: {skill_dir} (SKILL.md ~{body_tokens} tokens approx., {len(chapter_files)} chapter file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
