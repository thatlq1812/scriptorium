#!/usr/bin/env python3
"""Scaffold a new skill folder from a gold template. Stdlib only — no
dependency, no venv needed. Automates the folder/file mechanics only; the
actual authoring (filling every <...> slot in SKILL.md) still requires
elicited input + grounded research, per skill-creator's own precondition —
this script does not skip that step.

Usage:
    python scaffold_skill.py <skill_id> --template standalone_skill
    python scaffold_skill.py <skill_id> --template dependency_skill [--skills-dir ../../]
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

NAME_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
VALID_TEMPLATES = {"standalone_skill", "dependency_skill"}


def scaffold(skill_id: str, template: str, skills_dir: Path) -> Path:
    if not NAME_RE.match(skill_id):
        raise ValueError(
            f"'{skill_id}' doesn't match the agentskills.io name pattern "
            "(lowercase letters/numbers/hyphens, 3-64 chars, starts with a letter)."
        )
    if template not in VALID_TEMPLATES:
        raise ValueError(f"Unknown template '{template}'. Choose one of: {sorted(VALID_TEMPLATES)}")

    src = TEMPLATES_DIR / template
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    dest = skills_dir / skill_id
    if dest.exists():
        raise FileExistsError(f"skills/{skill_id} already exists — not overwriting.")

    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".gitkeep"))

    skill_md = dest / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    text = text.replace("<skill_id>", skill_id)
    skill_md.write_text(text, encoding="utf-8")

    # Recreate empty subfolders that shutil.ignore_patterns skipped copying
    # the .gitkeep marker for, so the structure is still visible on disk.
    for sub in ("scripts", "references"):
        subdir = dest / sub
        if (src / sub).exists() and not subdir.exists():
            subdir.mkdir()

    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skill_id")
    parser.add_argument("--template", required=True, choices=sorted(VALID_TEMPLATES))
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "skills",
        help="Defaults to the repo's skills/ directory (resolved relative to this script).",
    )
    args = parser.parse_args()

    try:
        dest = scaffold(args.skill_id, args.template, args.skills_dir)
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        sys.exit(str(exc))

    print(f"OK: scaffolded {dest} from template '{args.template}'")
    print("Next: fill every remaining <...> slot in SKILL.md, then delete all <!-- --> comment blocks.")
    print("Reminder: this only automates folder mechanics — elicited input + research still required before writing real content.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
