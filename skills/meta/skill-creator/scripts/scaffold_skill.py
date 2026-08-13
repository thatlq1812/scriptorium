#!/usr/bin/env python3
"""Scaffold a new skill folder from a gold template. Stdlib only — no
dependency, no venv needed. Automates the folder/file mechanics only; the
actual authoring (filling every <...> slot in SKILL.md) still requires
elicited input + grounded research, per skill-creator's own precondition —
this script does not skip that step.

Usage:
    python scaffold_skill.py <skill_id> --template standalone_skill --domain education
    python scaffold_skill.py <skill_id> --template dependency_skill --domain meta [--skills-dir ../../]

--domain places the new skill directly under skills/<domain>/<skill_id>/ (this
repo's domain-per-folder layout, 2026-08-13) -- matches registry/skills.json's
own mandatory tags.domain field (see registry/SCHEMA.md), and is NOT restricted
to a fixed list here: domain is an open, growing taxonomy (new occupation
verticals get added over time), so an unfamiliar value creates that domain
folder rather than being refused.
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


def scaffold(skill_id: str, template: str, skills_dir: Path, domain: str) -> Path:
    if not NAME_RE.match(skill_id):
        raise ValueError(
            f"'{skill_id}' doesn't match the agentskills.io name pattern "
            "(lowercase letters/numbers/hyphens, 3-64 chars, starts with a letter)."
        )
    if template not in VALID_TEMPLATES:
        raise ValueError(f"Unknown template '{template}'. Choose one of: {sorted(VALID_TEMPLATES)}")
    if not NAME_RE.match(domain):
        raise ValueError(f"'{domain}' doesn't look like a valid domain folder name (lowercase letters/numbers/hyphens).")

    # Refuse if skill_id already exists under ANY domain folder -- skill_id must
    # be globally unique regardless of which domain it's filed under.
    existing = next(skills_dir.glob(f"*/{skill_id}"), None)
    if existing is not None:
        raise FileExistsError(f"'{skill_id}' already exists at {existing} — not overwriting.")

    src = TEMPLATES_DIR / template
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    dest = skills_dir / domain / skill_id
    if dest.exists():
        raise FileExistsError(f"skills/{domain}/{skill_id} already exists — not overwriting.")

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
        "--domain", required=True,
        help="Domain folder to scaffold into (skills/<domain>/<skill_id>/) -- matches "
             "registry/skills.json's tags.domain. Not restricted to a fixed list.",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Defaults to the repo's skills/ directory (resolved relative to this script).",
    )
    args = parser.parse_args()

    try:
        dest = scaffold(args.skill_id, args.template, args.skills_dir, args.domain)
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        sys.exit(str(exc))

    print(f"OK: scaffolded {dest} from template '{args.template}'")
    print("Next: fill every remaining <...> slot in SKILL.md, then delete all <!-- --> comment blocks.")
    print("Reminder: this only automates folder mechanics — elicited input + research still required before writing real content.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
