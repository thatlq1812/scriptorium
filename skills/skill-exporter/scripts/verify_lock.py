#!/usr/bin/env python3
"""Verify a bundle's skills.lock against the current skills/ directory (or
a re-exported bundle) -- did the actual content of each locked skill change
since the bundle was exported?

Usage:
    python verify_lock.py <skills.lock> [--skills-dir <path>]

Exit 0 = every locked skill's content hash still matches, 1 = at least one
mismatch/missing skill (all printed), 2 = malformed lock file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2].parent
DEFAULT_SKILLS_DIR = REPO_ROOT / "skills"


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lock_path")
    parser.add_argument("--skills-dir", default=None)
    args = parser.parse_args()

    lock_path = Path(args.lock_path)
    if not lock_path.exists():
        print(f"ERROR: lock file not found: {lock_path}", file=sys.stderr)
        return 2
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: malformed lock file: {e}", file=sys.stderr)
        return 2
    if not isinstance(lock, dict) or not lock:
        print("ERROR: lock file must be a non-empty object of skill_id -> {version, content_sha256}", file=sys.stderr)
        return 2

    skills_dir = Path(args.skills_dir) if args.skills_dir else DEFAULT_SKILLS_DIR

    mismatches: list[str] = []
    for skill_id, info in lock.items():
        if not isinstance(info, dict) or "content_sha256" not in info or "version" not in info:
            mismatches.append(f"{skill_id}: malformed lock entry (missing 'version' or 'content_sha256')")
            continue
        skill_dir = skills_dir / skill_id
        if not skill_dir.is_dir():
            mismatches.append(f"{skill_id}: not found under {skills_dir}")
            continue
        actual_hash = _content_sha256(skill_dir)
        if actual_hash != info["content_sha256"]:
            mismatches.append(
                f"{skill_id}: content changed since lock (locked {info['content_sha256'][:12]}..., "
                f"now {actual_hash[:12]}...)"
            )

    if mismatches:
        print(f"MISMATCH ({len(mismatches)} skill(s)):", file=sys.stderr)
        for m in mismatches:
            print(f"  - {m}", file=sys.stderr)
        return 1

    print(f"OK: all {len(lock)} locked skill(s) match {skills_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
