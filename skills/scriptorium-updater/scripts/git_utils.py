"""Shared subprocess-git wrapper for all 3 scripts in this skill -- never
duplicate this, a real bug already happened once this same session
(html-poster-composer's CSS) from two copies of the same logic drifting
apart.

stdin=subprocess.DEVNULL is load-bearing, not defensive boilerplate: a
real cold-agent test (2026-08-07) found `git pull` hanging indefinitely
when invoked from a non-interactive/piped calling context, because
`subprocess.run()` with no explicit `stdin` inherits the PARENT's stdin --
git's credential helper (e.g. Windows GCM) can then try to prompt
interactively on that inherited stdin and block forever with zero error
message, the exact "silent hang" failure class this project's discipline
refuses everywhere else. Explicitly closing stdin makes any credential
prompt fail FAST and loudly instead (git errors out immediately when it
can't read a prompt response), never hang.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(repo_dir: Path | None, args: list[str]) -> subprocess.CompletedProcess:
    cmd = ["git", "-C", str(repo_dir), *args] if repo_dir is not None else ["git", *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
