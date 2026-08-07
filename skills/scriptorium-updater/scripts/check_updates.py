#!/usr/bin/env python3
"""Checks whether a local Scriptorium clone is behind its origin remote,
and if so, WHICH skills actually changed (not just "there are new
commits") -- by diffing registry/skills.json's skill_id->version map
between the local HEAD and origin/master. Read-only: runs `git fetch`
(updates remote-tracking refs only, never touches the working tree) plus
`git show`/`git diff --name-only` reads. Never pulls, never writes to the
skills/ directory -- that's `sync_skills.py`'s job, a separate explicit
step, matching every bootstrap skill's check-then-apply discipline in this
registry (python-env-bootstrap, browser-web-renderer, ffmpeg-bootstrap...).

This script only REPORTS. Per owner direction (2026-08-07): what a caller
does with the report -- e.g. a skill_id present locally but no longer in
registry/skills.json -- is a judgment call for the calling agent to make
by reading this report, not something this script decides or acts on.

Usage:
    python check_updates.py <source_repo_dir> [--branch origin/master]

Exit 0 = check completed (see the printed report's "up_to_date" field for
the actual answer), 2 = source_repo_dir isn't a git repo / git itself
failed / malformed args.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from git_utils import run_git  # noqa: E402


def _version_map(repo_dir: Path, ref: str) -> dict[str, str] | None:
    result = run_git(repo_dir, ["show", f"{ref}:registry/skills.json"])
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return {s["skill_id"]: s.get("version", "?") for s in data.get("skills", []) if "skill_id" in s}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source_repo_dir", type=Path)
    parser.add_argument("--branch", default="origin/master")
    args = parser.parse_args()

    if not (args.source_repo_dir / ".git").exists():
        print(f"ERROR: {args.source_repo_dir} is not a git repository (no .git found).", file=sys.stderr)
        return 2

    fetch = run_git(args.source_repo_dir, ["fetch", "origin"])
    if fetch.returncode != 0:
        print(f"ERROR: git fetch failed: {fetch.stderr.strip()}", file=sys.stderr)
        return 2

    local_rev = run_git(args.source_repo_dir, ["rev-parse", "HEAD"])
    if local_rev.returncode != 0:
        print(f"ERROR: could not resolve HEAD: {local_rev.stderr.strip()}", file=sys.stderr)
        return 2
    local_head = local_rev.stdout.strip()

    remote_rev = run_git(args.source_repo_dir, ["rev-parse", args.branch])
    # git rev-parse on an unresolvable ref exits non-zero but still echoes the raw
    # argument to stdout (a real quirk found via adversarial testing) -- checking
    # returncode explicitly, not just "is stdout non-empty", is load-bearing here.
    if remote_rev.returncode != 0:
        print(f"ERROR: could not resolve {args.branch!r} -- does this clone track that remote/branch? ({remote_rev.stderr.strip()})", file=sys.stderr)
        return 2
    remote_head = remote_rev.stdout.strip()

    up_to_date = local_head == remote_head

    changed_skill_dirs: list[str] = []
    version_changes: list[dict] = []
    if not up_to_date:
        diff = run_git(args.source_repo_dir, ["diff", "--name-only", "HEAD", args.branch, "--", "skills/"])
        changed_files = [line for line in diff.stdout.splitlines() if line.strip()]
        changed_skill_dirs = sorted({line.split("/", 2)[1] for line in changed_files if line.startswith("skills/") and len(line.split("/")) > 1})

        local_versions = _version_map(args.source_repo_dir, "HEAD") or {}
        remote_versions = _version_map(args.source_repo_dir, args.branch) or {}
        all_ids = sorted(set(local_versions) | set(remote_versions))
        for skill_id in all_ids:
            old_v, new_v = local_versions.get(skill_id), remote_versions.get(skill_id)
            if old_v != new_v:
                version_changes.append({"skill_id": skill_id, "local_version": old_v, "remote_version": new_v})

    report = {
        "up_to_date": up_to_date,
        "local_commit": local_head,
        "remote_commit": remote_head,
        "changed_skill_dirs": changed_skill_dirs,
        "version_changes": version_changes,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
