#!/usr/bin/env python3
"""Package one or more skills from skills/ into a single .zip a recipient
can drop into their own agent project -- copies each skill's whole folder
(SKILL.md + scripts/ + assets/ + references/), auto-resolves any
registry-declared dependency that is itself a skill_id in this registry
(recursively), and writes a MANIFEST.md at the zip root listing everything
included, real version/status fields, and any non-skill dependency (e.g. a
PyPI package pin) the recipient still needs to install themselves.

Stdlib only (json, argparse, zipfile, shutil), local, deterministic -- no
network, no AI call.

HARD EXCLUSION (same rule as list_candidates.py, enforced again here --
never trust that a caller already ran list_candidates.py first): a
requested skill_id with license_debt != null or security_audit.status !=
"passed" is refused, the whole export fails, nothing is written. This is
not a per-skill skip -- an export bundle either fully honors the rule or
doesn't happen.

Exit codes: 0 = exported, 1 = a requested skill_id doesn't exist or fails
the hard-exclusion rule, 2 = malformed registry / output already exists.

Usage:
    python export_bundle.py <skill_id> [<skill_id> ...] -o bundle.zip [--for "description"] [--force]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2].parent
REGISTRY_PATH = REPO_ROOT / "registry" / "skills.json"
SKILLS_DIR = REPO_ROOT / "skills"


def load_registry() -> dict[str, dict]:
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"MALFORMED registry: {exc}", file=sys.stderr)
        raise SystemExit(2)
    skills = data.get("skills") if isinstance(data, dict) else data
    if not isinstance(skills, list):
        print("MALFORMED registry: expected a list of skills (top-level or under 'skills')", file=sys.stderr)
        raise SystemExit(2)
    return {s["skill_id"]: s for s in skills}


def is_exportable(skill: dict) -> tuple[bool, str]:
    if skill.get("license_debt") is not None:
        return False, "license_debt is set -- may not be distributed outside the internal repo"
    audit = skill.get("security_audit", {})
    if audit.get("status") != "passed":
        return False, f"security_audit.status is {audit.get('status')!r}, not 'passed'"
    return True, ""


def resolve_with_dependencies(requested: list[str], registry: dict[str, dict]) -> tuple[list[str], list[str]]:
    """Returns (skill_ids_to_include, non_skill_dependency_strings), expanding
    any dependency string that is itself a registry skill_id, recursively."""
    included: list[str] = []
    non_skill_deps: set[str] = set()
    seen: set[str] = set()
    queue = list(requested)

    while queue:
        skill_id = queue.pop(0)
        if skill_id in seen:
            continue
        seen.add(skill_id)
        skill = registry.get(skill_id)
        if skill is None:
            print(f"REFUSED: skill_id {skill_id!r} not found in registry.", file=sys.stderr)
            raise SystemExit(1)
        ok, reason = is_exportable(skill)
        if not ok:
            print(f"REFUSED: {skill_id!r} cannot be exported -- {reason}", file=sys.stderr)
            raise SystemExit(1)
        included.append(skill_id)
        for dep in skill.get("dependencies", []):
            if dep in registry:
                queue.append(dep)
            else:
                non_skill_deps.add(dep)

    return included, sorted(non_skill_deps)


def build_manifest(purpose: str | None, included: list[str], non_skill_deps: list[str], registry: dict[str, dict]) -> str:
    lines = ["# Skill Bundle", ""]
    if purpose:
        lines += [f"**Purpose**: {purpose}", ""]
    lines += ["## Skills included", ""]
    for skill_id in included:
        s = registry[skill_id]
        tags = s.get("tags", {})
        lines.append(
            f"- **{skill_id}** v{s['version']} "
            f"(domain={tags.get('domain', [])}, task_type={tags.get('task_type', [])}, "
            f"risk_tier={tags.get('risk_tier')}, security_audit={s.get('security_audit', {}).get('status')})"
        )
    if non_skill_deps:
        lines += ["", "## Non-skill dependencies to install yourself", ""]
        for dep in non_skill_deps:
            lines.append(f"- `{dep}`")
    lines += [
        "",
        "## How to use",
        "",
        "Drop the `skills/` folder from this bundle into your own project's `skills/` directory. "
        "Each skill's own `SKILL.md` documents how to run it and any environment setup it needs "
        "(e.g. `python-env-bootstrap` for the shared Python venv, if a dependency above names it).",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skill_ids", nargs="+")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--for", dest="purpose", default=None, help="short description of who/what this bundle is for, written into MANIFEST.md")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.output.exists() and not args.force:
        print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
        return 2

    registry = load_registry()
    included, non_skill_deps = resolve_with_dependencies(args.skill_ids, registry)

    manifest = build_manifest(args.purpose, included, non_skill_deps, registry)

    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("MANIFEST.md", manifest)
        for skill_id in included:
            skill_dir = SKILLS_DIR / skill_id
            if not skill_dir.is_dir():
                print(f"REFUSED: {skill_id!r} is in the registry but skills/{skill_id}/ doesn't exist on disk.", file=sys.stderr)
                return 1
            for path in skill_dir.rglob("*"):
                if path.is_dir() or "__pycache__" in path.parts:
                    continue
                arcname = Path("skills") / path.relative_to(SKILLS_DIR)
                zf.write(path, arcname)

    print(f"OK: {len(included)} skill(s) -> {args.output}")
    for skill_id in included:
        extra = " (auto-included dependency)" if skill_id not in args.skill_ids else ""
        print(f"  - {skill_id}{extra}")
    if non_skill_deps:
        print(f"NOTE: {len(non_skill_deps)} non-skill dependency(ies) not bundled, listed in MANIFEST.md: {non_skill_deps}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
