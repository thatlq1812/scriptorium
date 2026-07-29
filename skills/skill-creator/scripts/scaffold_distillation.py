#!/usr/bin/env python3
"""Scaffold the directory/file structure for a document-distillation skill
(tacit-knowledge extraction from a book/manual/document folder into an
on-demand-reference skill).

This only automates the folder/file mechanics -- same "scaffold, don't skip
the precondition" posture as scaffold_skill.py. The actual chapter-summary
content (frameworks, mental models, worked examples, decision rules) is
agent-authored, requiring real reading comprehension of the source
document -- see SKILL.md's "Document Distillation Mode" section for the
step-by-step the calling agent follows after this script runs.

Shape (chapters/ dir + glossary.md/patterns.md/cheatsheet.md + master
SKILL.md stub) is adapted from a real, cloned reference project's own
documented output structure (outside_research/references/book-to-skill,
MIT, license-compliance-checked) -- not invented from scratch. See that
skill's own SKILL.md Step 6-9 for the source of this shape.

Usage:
    python scaffold_distillation.py <skill_id> --chapters <n> [--skills-dir <path>] [--force]

Exit 0 = scaffolded, 1 = target already exists (no --force), 2 = bad arguments.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

NAME_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")

CHAPTER_STUB_TEMPLATE = """# Chapter {n:02d}: <Full Title>

## Core Idea
<1-2 sentences: the single most important thing this chapter teaches>

## Frameworks Introduced
- **<Framework Name>**: <exact formulation -- preserve the source author's naming>
  - When to use: <specific situation>
  - How: <steps or criteria>

## Key Concepts
- **<Term>**: <precise definition in 1 sentence>

## Key Takeaways
1. <Actionable insight>

## Connects To
- **Ch NN**: <why this chapter relates -- must reference a real chapter file that exists>
"""

GLOSSARY_STUB = "# Glossary\n\n<!-- **Term** -- definition (Ch NN). Alphabetically sorted. -->\n"
PATTERNS_STUB = "# Patterns\n\n<!-- ## Pattern Name\n**When to use**: ...\n**How**: ...\n**Trade-offs**: ... -->\n"
CHEATSHEET_STUB = "# Cheatsheet\n\n<!-- Decision rules, thresholds, tells -- not bare term/definition rows. -->\n"

SKILL_MD_STUB = """---
name: {skill_id}
description: "<what this distilled skill teaches, and when to use it -- fill after chapters are written>"
license: MIT
compatibility: Portable per the agentskills.io open spec.
metadata:
  domain: general
  task_type: research
  risk_tier: N1
  source: self-authored
  elicited_from: "Distilled from <source document title/author> via skill-creator's Document Distillation Mode (UPGRADE_PLAN_20260729.md Item 5)."
  version: 0.1.0
  grounding: required
  object_type: []
---

# {skill_id}

<!-- Master index. Keep under ~4000 tokens -- this file is always loaded;
     chapters/glossary/patterns/cheatsheet are loaded on-demand. Most
     important content first: compaction truncates from the end. -->

## Chapters

<!-- One line per chapter, pointing into chapters/ -->
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_id")
    parser.add_argument("--chapters", type=int, required=True, help="Number of chapter stub files to create")
    parser.add_argument("--skills-dir", default=None, help="Defaults to <repo_root>/skills relative to this script")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not NAME_RE.match(args.skill_id):
        print(f"ERROR: '{args.skill_id}' doesn't match the agentskills.io name pattern.", file=sys.stderr)
        return 2
    if args.chapters < 1:
        print("ERROR: --chapters must be >= 1.", file=sys.stderr)
        return 2

    skills_dir = Path(args.skills_dir) if args.skills_dir else Path(__file__).resolve().parent.parent.parent
    target = skills_dir / args.skill_id

    if target.exists() and not args.force:
        print(f"ERROR: {target} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    chapters_dir = target / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    for n in range(1, args.chapters + 1):
        chapter_path = chapters_dir / f"ch{n:02d}-untitled.md"
        chapter_path.write_text(CHAPTER_STUB_TEMPLATE.format(n=n), encoding="utf-8", newline="\n")

    (target / "glossary.md").write_text(GLOSSARY_STUB, encoding="utf-8", newline="\n")
    (target / "patterns.md").write_text(PATTERNS_STUB, encoding="utf-8", newline="\n")
    (target / "cheatsheet.md").write_text(CHEATSHEET_STUB, encoding="utf-8", newline="\n")
    (target / "SKILL.md").write_text(SKILL_MD_STUB.format(skill_id=args.skill_id), encoding="utf-8", newline="\n")

    print(f"Scaffolded {target}")
    print(f"  chapters/: {args.chapters} stub file(s)")
    print("  glossary.md, patterns.md, cheatsheet.md, SKILL.md stubs created")
    print("Next: fill every <...> placeholder from real source-document content (agent-authored, not scripted).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
