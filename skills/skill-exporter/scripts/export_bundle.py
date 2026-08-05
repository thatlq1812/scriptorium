#!/usr/bin/env python3
"""Package one or more skills from skills/ into a single .zip a recipient
can drop into their own agent project -- copies each skill's whole folder
(SKILL.md + scripts/ + assets/ + references/), auto-resolves any
registry-declared dependency that is itself a skill_id in this registry
(recursively), and writes MANIFEST.md, dependency-tree.md, and skills.lock
at the zip root.

Stdlib only (json, argparse, zipfile, shutil, hashlib), local, deterministic
-- no network, no AI call.

HARD EXCLUSION (same rule as list_candidates.py, enforced again here --
never trust that a caller already ran list_candidates.py first): a
requested skill_id with license_debt != null, security_audit.status !=
"passed", or operational_status.state == "paused" (added 2026-07-29, see
registry/SCHEMA.md) is refused, the whole export fails, nothing is written.
This is not a per-skill skip -- an export bundle either fully honors the
rule or doesn't happen.

NEGATIVE DEPENDENCIES (--exclude, added v0.2.0): remove a skill from an
otherwise-resolved bundle by exact skill_id or by tag pattern
("domain:education", "task_type:drafting"). If an excluded skill turns out
to be a hard dependency of a still-included skill, the whole export is
refused (exit 1) rather than silently shipping a bundle whose dependency
chain is broken -- same "whole bundle or nothing" posture as the
license_debt/security_audit exclusion.

skills.lock (added v0.2.0): a JSON manifest of skill_id -> {version,
content_sha256} for every included skill, written into the bundle. Lets a
recipient (or this project later) verify a bundle's exact contents against
the current registry via verify_lock.py -- the same reproducibility idea as
package-lock.json/Cargo.lock, adapted to a plain content hash since skills
have no package registry to pin a version against.

Exit codes: 0 = exported, 1 = a requested skill_id doesn't exist, fails the
hard-exclusion rule, or an --exclude removes a hard dependency, 2 =
malformed registry / output already exists.

Usage:
    python export_bundle.py <skill_id> [<skill_id> ...] -o bundle.zip \\
        [--for "description"] [--exclude domain:education] [--exclude some-skill-id] [--force]
"""
from __future__ import annotations

import argparse
import hashlib
import json
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
    op_status = skill.get("operational_status")
    if isinstance(op_status, dict) and op_status.get("state") == "paused":
        return False, f"operational_status is paused -- {op_status.get('reason', 'no reason recorded')}"
    return True, ""


def resolve_with_dependencies(requested: list[str], registry: dict[str, dict]) -> tuple[list[str], list[str], dict[str, str]]:
    """Returns (skill_ids_to_include, non_skill_dependency_strings, reasons).
    reasons maps skill_id -> 'requested' or 'dependency of <parent>' (first
    parent found, for a readable dependency-tree -- a skill reachable via
    multiple paths only records the first)."""
    included: list[str] = []
    non_skill_deps: set[str] = set()
    seen: set[str] = set()
    reasons: dict[str, str] = {}
    queue: list[tuple[str, str | None]] = [(sid, None) for sid in requested]

    while queue:
        skill_id, parent = queue.pop(0)
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
        reasons[skill_id] = "requested" if parent is None else f"dependency of {parent}"
        for dep in skill.get("dependencies", []):
            if dep in registry:
                queue.append((dep, skill_id))
            else:
                non_skill_deps.add(dep)

    return included, sorted(non_skill_deps), reasons


def _matches_exclude_pattern(skill_id: str, skill: dict, pattern: str) -> bool:
    if pattern == skill_id:
        return True
    if ":" in pattern:
        axis, value = pattern.split(":", 1)
        tag_values = skill.get("tags", {}).get(axis)
        if isinstance(tag_values, list):
            return value in tag_values
        return tag_values == value
    return False


def apply_exclusions(
    included: list[str], reasons: dict[str, str], exclude_patterns: list[str], registry: dict[str, dict]
) -> list[str]:
    if not exclude_patterns:
        return included

    to_remove = {
        sid for sid in included
        if any(_matches_exclude_pattern(sid, registry[sid], pat) for pat in exclude_patterns)
    }
    if not to_remove:
        return included

    remaining = [sid for sid in included if sid not in to_remove]
    remaining_set = set(remaining)

    for sid in remaining:
        for dep in registry[sid].get("dependencies", []):
            if dep in to_remove:
                print(
                    f"REFUSED: --exclude removed {dep!r}, but it is a hard dependency of "
                    f"{sid!r} (still included) -- would produce a broken bundle. "
                    f"Either exclude {sid!r} too, or don't exclude {dep!r}.",
                    file=sys.stderr,
                )
                raise SystemExit(1)

    print(f"Excluded {len(to_remove)} skill(s): {sorted(to_remove)}")
    return remaining


def _content_sha256(skill_dir: Path) -> str:
    hasher = hashlib.sha256()
    files = sorted(
        p for p in skill_dir.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )
    for path in files:
        rel = path.relative_to(skill_dir).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def build_manifest(purpose: str | None, included: list[str], non_skill_deps: list[str], reasons: dict[str, str], registry: dict[str, dict]) -> str:
    lines = ["# Skill Bundle", ""]
    if purpose:
        lines += [f"**Purpose**: {purpose}", ""]
    lines += ["## Skills included", ""]
    for skill_id in included:
        s = registry[skill_id]
        tags = s.get("tags", {})
        lines.append(
            f"- **{skill_id}** v{s['version']} ({reasons.get(skill_id, 'requested')}) "
            f"(domain={tags.get('domain', [])}, task_type={tags.get('task_type', [])}, "
            f"risk_tier={tags.get('risk_tier')}, security_audit={s.get('security_audit', {}).get('status')})"
        )
    if non_skill_deps:
        lines += ["", "## Non-skill dependencies to install yourself", ""]
        for dep in non_skill_deps:
            lines.append(f"- `{dep}`")
    lines += [
        "",
        "## Where to install",
        "",
        "Different agent harnesses look for skills in different directories -- there is no single "
        "universal path, and this bundle doesn't know which harness will consume it at export time. "
        "Known conventions:",
        "",
        "- **Claude Code**: `.claude/skills/<skill_id>/`",
        "- **goose (Agent Client Protocol)**: `.agents/skills/<skill_id>/` (also checks "
        "`.goose/skills/` and `.claude/skills/` project-local, plus a few global paths under "
        "`$HOME` -- reported from real testing, not independently verified in this repo)",
        "- **Cursor**: `.cursor/skills/<skill_id>/` (per Cursor's own docs -- not independently "
        "verified in this repo)",
        "",
        "This bundle ships every skill under a flat `skills/<skill_id>/` folder at the zip root. "
        "Copy (or symlink/junction) each skill's folder into whichever directory your harness "
        "actually scans, then don't leave a second copy under this bundle's own `skills/` path lying "
        "around where your harness might also pick it up -- two registrations of the same skill_id "
        "is a conflict, not redundancy. If you're not sure which directory your harness uses, check "
        "its own docs.",
        "",
        "## How to use",
        "",
        "Each skill's own `SKILL.md` documents how to run it and any environment setup it needs "
        "(e.g. `python-env-bootstrap` for the shared Python venv, if a dependency above names it). "
        "See `dependency-tree.md` for why each skill is here, and `skills.lock` if you need to "
        "verify this bundle's exact contents later.",
        "",
        "## Note for the agent using this bundle",
        "",
        "These skills are curated as a set for one real workflow, not a random assortment — "
        "several are designed to chain (one skill's output feeds the next skill's input; see "
        "`dependency-tree.md` and each `SKILL.md`'s own cross-references, e.g. \"Chains into\" "
        "sections). A generic \"minimize tool calls\" instinct from your own system prompt does "
        "not apply here: invoking multiple skills in sequence for one task is the intended usage "
        "pattern, not wasteful — each skill deliberately does one narrow thing so a real multi-step "
        "task composes several of them, the same way you'd chain multiple shell commands in a real "
        "pipeline rather than write one giant script. Treat a skill dependency in this bundle as a "
        "signal to actually use the dependency, not just a licensing/packaging technicality.",
    ]
    return "\n".join(lines) + "\n"


def build_dependency_tree(requested: list[str], included: list[str], reasons: dict[str, str]) -> str:
    lines = ["# Dependency Tree", "", "Why each skill in this bundle is here.", ""]
    for skill_id in requested:
        if skill_id in included:
            lines.append(f"- **{skill_id}** — requested")
    auto_included = [sid for sid in included if sid not in requested]
    if auto_included:
        lines += ["", "## Auto-included dependencies", ""]
        for skill_id in auto_included:
            lines.append(f"- **{skill_id}** — {reasons.get(skill_id, 'dependency')}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skill_ids", nargs="+")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--for", dest="purpose", default=None, help="short description of who/what this bundle is for, written into MANIFEST.md")
    parser.add_argument(
        "--exclude", action="append", default=[],
        help="Exact skill_id, or 'axis:value' tag pattern (e.g. domain:education). Repeatable.",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.output.exists() and not args.force:
        print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
        return 2

    registry = load_registry()
    included, non_skill_deps, reasons = resolve_with_dependencies(args.skill_ids, registry)
    included = apply_exclusions(included, reasons, args.exclude, registry)

    manifest = build_manifest(args.purpose, included, non_skill_deps, reasons, registry)
    dep_tree = build_dependency_tree(args.skill_ids, included, reasons)

    lock = {
        skill_id: {
            "version": registry[skill_id]["version"],
            "content_sha256": _content_sha256(SKILLS_DIR / skill_id),
        }
        for skill_id in included
    }

    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("MANIFEST.md", manifest)
        zf.writestr("dependency-tree.md", dep_tree)
        zf.writestr("skills.lock", json.dumps(lock, ensure_ascii=False, indent=2) + "\n")
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
        extra = f" ({reasons.get(skill_id)})" if skill_id not in args.skill_ids else ""
        print(f"  - {skill_id}{extra}")
    if non_skill_deps:
        print(f"NOTE: {len(non_skill_deps)} non-skill dependency(ies) not bundled, listed in MANIFEST.md: {non_skill_deps}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
