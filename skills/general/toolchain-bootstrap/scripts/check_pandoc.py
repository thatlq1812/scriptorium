#!/usr/bin/env python3
"""Detect whether `pandoc` is available on this machine. Read-only --
never installs anything itself; that's install_pandoc.ps1/.sh, run only
when explicitly asked (it's a system package-manager install).

.tex/.docx/.html conversions work with pandoc alone. Converting TO pdf
additionally needs a working LaTeX engine (see check_xelatex.py, this same skill) -- this
script reports that dependency but doesn't check for xelatex itself, to
keep the two bootstrap skills independently useful.

Stdlib only (shutil, subprocess, platform, sys).

Exit codes: 0 = pandoc found, 1 = not found (install command printed for
this platform, nothing installed by this script).

Usage:
    python check_pandoc.py
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

INSTALL_HINTS = {
    "Windows": "winget install --id JohnMacFarlane.Pandoc -e   (or run install_pandoc.ps1)",
    "Darwin": "brew install pandoc   (or run install_pandoc.sh)",
    "Linux": "sudo apt-get install -y pandoc   (or run install_pandoc.sh)",
}


def main() -> int:
    path = shutil.which("pandoc")
    if not path:
        system = platform.system()
        hint = INSTALL_HINTS.get(system, "no known install hint for this platform -- install pandoc manually from https://pandoc.org/installing.html")
        print("[MISSING] pandoc not found on PATH", file=sys.stderr)
        print(f"Suggested install ({system}): {hint}", file=sys.stderr)
        print("Nothing was installed by this script -- detection only.", file=sys.stderr)
        return 1

    try:
        result = subprocess.run(["pandoc", "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10)
        version_line = result.stdout.splitlines()[0] if result.stdout else "unknown version"
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"[MISSING] pandoc found at {path} but failed to run: {exc}", file=sys.stderr)
        return 1

    print(f"[OK] pandoc: {path} ({version_line})")
    print("Note: converting TO .pdf additionally needs a working LaTeX engine -- see check_xelatex.py (this same skill) if that's needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
