#!/usr/bin/env python3
"""Detect whether a Typst binary is available -- checked in this priority
order: (1) the shared repo-local location `<repo_root>/.tools/typst/`
(mirrors python-env-bootstrap's shared `.venv/` pattern -- a single portable
binary every Typst-dependent skill can reuse, gitignored, never committed),
(2) PATH. Read-only -- never installs anything itself; that's
install_typst.py, run only when explicitly asked (it downloads ~50MB from
GitHub).

Stdlib only (shutil, subprocess, platform, sys) -- subprocess only runs
`typst --version`, fixed argument list, no shell=True.

Exit codes: 0 = typst found (shared location or PATH), 1 = not found.

Usage:
    python check_typst.py
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[4]
SHARED_TYPST_DIR = REPO_ROOT / ".tools" / "typst"


def _binary_name() -> str:
    return "typst.exe" if platform.system() == "Windows" else "typst"


def find_typst() -> str | None:
    shared = SHARED_TYPST_DIR / _binary_name()
    if shared.is_file():
        return str(shared)
    return shutil.which("typst")


def main() -> int:
    path = find_typst()
    if path is None:
        print("[MISSING] typst not found in .tools/typst/ or PATH.", file=sys.stderr)
        print(
            "Suggested: python skills/general/typst-bootstrap/scripts/install_typst.py "
            "(downloads the official static binary from github.com/typst/typst releases "
            f"into {SHARED_TYPST_DIR}, no system package manager, no system-wide install).",
            file=sys.stderr,
        )
        print("Nothing was installed by this script -- detection only.", file=sys.stderr)
        return 1

    try:
        result = subprocess.run([path, "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10)
        version_line = (result.stdout or result.stderr).strip().splitlines()[0] if (result.stdout or result.stderr) else "unknown version"
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"[MISSING] typst found at {path} but failed to run: {exc}", file=sys.stderr)
        return 1

    print(f"[OK] typst: {path} ({version_line})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
