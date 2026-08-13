#!/usr/bin/env python3
"""Pulls the latest Scriptorium source and copies its skills/ folder into a
caller's own project skills directory (e.g. .claude/skills/, .agents/skills/
-- the exact path is harness-specific, see html-poster-composer's sibling
skill-exporter's own "Where to install" convention; this script does not
guess it, the caller passes the real target).

ADD/UPDATE ONLY -- never deletes anything at the destination. A skill_id
present at the destination but no longer under the source's skills/ is
reported (see "destination_only" in the output), never removed
automatically. Owner direction (2026-08-07): "agent phía user có thể tự xử
lý case đó... do agent làm theo ghi chú" -- this script's job ends at
producing an accurate, structured report; deciding what to do about an
anomaly like that is the calling agent's judgment call, not a hardcoded
rule here. Matches this registry's own established 2-step discipline
(a script proposes/reports, the reviewing agent decides) applied to sync
instead of content structuring.

Usage:
    python sync_skills.py <source_repo_dir> <dest_skills_dir> [--dry-run]

Exit 0 = sync completed (or dry-run report printed, nothing written),
1 = source_repo_dir has uncommitted local changes (refuses to pull over
them) or `git pull` itself failed, 2 = malformed args / source_repo_dir
isn't a git repo / source has no skills/ directory.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from git_utils import run_git  # noqa: E402


def _enumerate_source_skills(source_skills_dir: Path) -> dict[str, Path]:
    """skill_id -> its real source directory. Auto-detects flat (skills/<id>/,
    legacy) vs domain-nested (skills/<domain>/<id>/, this repo since 2026-08-13)
    layout per top-level child, so a source clone pulled from origin before
    origin itself gets the domain-reorg push still syncs correctly."""
    result: dict[str, Path] = {}
    for child in sorted(source_skills_dir.iterdir()):
        if not child.is_dir():
            continue
        if (child / "SKILL.md").is_file():
            result[child.name] = child
            continue
        for grandchild in sorted(child.iterdir()):
            if grandchild.is_dir() and (grandchild / "SKILL.md").is_file():
                result[grandchild.name] = grandchild
    return result


def _skill_version(skill_md_path: Path) -> str | None:
    if not skill_md_path.is_file():
        return None
    for line in skill_md_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("version:"):
            return stripped.split(":", 1)[1].strip().strip("'\"")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source_repo_dir", type=Path)
    parser.add_argument("dest_skills_dir", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing anything.")
    args = parser.parse_args()

    if not (args.source_repo_dir / ".git").exists():
        print(f"ERROR: {args.source_repo_dir} is not a git repository (no .git found).", file=sys.stderr)
        return 2
    source_skills_dir = args.source_repo_dir / "skills"
    if not source_skills_dir.is_dir():
        print(f"ERROR: {source_skills_dir} not found -- is source_repo_dir a real Scriptorium clone?", file=sys.stderr)
        return 2

    status = run_git(args.source_repo_dir, ["status", "--porcelain"])
    if status.stdout.strip():
        print(
            f"REFUSED: {args.source_repo_dir} has uncommitted local changes -- refusing to pull over them. "
            "Commit, stash, or discard them first (this is your SOURCE clone, not your own project).",
            file=sys.stderr,
        )
        return 1

    # Pulling the SOURCE clone happens even in --dry-run: it's a safe, non-destructive
    # fast-forward-only update to a dedicated mirror clone (already confirmed clean
    # above), not the thing --dry-run is meant to protect -- the DESTINATION write
    # (the copytree loop below) is. A dry-run that skipped this would report against
    # a stale source and silently under-report what would actually change.
    pull = run_git(args.source_repo_dir, ["pull", "--ff-only"])
    if pull.returncode != 0:
        print(f"ERROR: git pull failed: {pull.stderr.strip()}", file=sys.stderr)
        return 1

    dest = args.dest_skills_dir
    source_map = _enumerate_source_skills(source_skills_dir)
    source_skill_ids = sorted(source_map.keys())
    # Destination stays FLAT regardless of source layout -- it's the caller's own
    # harness skill directory (.claude/skills/, .agents/skills/, ...), which has
    # no concept of this repo's internal domain taxonomy (matches skill-exporter's
    # bundles, which are always written flat for the same reason).
    dest_skill_ids = sorted(p.name for p in dest.iterdir() if p.is_dir()) if dest.is_dir() else []

    added: list[str] = []
    updated: list[dict] = []
    unchanged: list[str] = []

    for skill_id in source_skill_ids:
        src_dir = source_map[skill_id]
        dst_dir = dest / skill_id
        src_version = _skill_version(src_dir / "SKILL.md")
        if not dst_dir.exists():
            added.append(skill_id)
            if not args.dry_run:
                shutil.copytree(src_dir, dst_dir)
            continue
        dst_version = _skill_version(dst_dir / "SKILL.md")
        if src_version != dst_version:
            updated.append({"skill_id": skill_id, "old_version": dst_version, "new_version": src_version})
        else:
            unchanged.append(skill_id)
        if not args.dry_run:
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)  # add/update only -- never removes an existing dest-only file

    destination_only = sorted(set(dest_skill_ids) - set(source_skill_ids))

    report = {
        "dry_run": args.dry_run,
        "added": added,
        "updated": updated,
        "unchanged_count": len(unchanged),
        "destination_only": destination_only,
    }
    print(json.dumps(report, indent=2))
    if destination_only:
        print(
            f"NOTE: {len(destination_only)} skill(s) exist at the destination but not in this source sync -- "
            "NOT removed (add/update only). Decide for yourself whether each is your own local addition to keep, "
            "or a skill retired upstream: " + ", ".join(destination_only),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
