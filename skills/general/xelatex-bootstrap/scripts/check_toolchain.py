#!/usr/bin/env python3
"""Detect whether the XeLaTeX toolchain (xelatex + biber + the fontspec
LaTeX package) is available on this machine. Read-only -- never installs
anything itself; that's install_toolchain.ps1/.sh, run only when explicitly
asked (it invokes a system package manager and can be a multi-GB, several-
minute operation).

Stdlib only (shutil, subprocess, platform, sys) -- subprocess is used only
to run `xelatex --version` / `biber --version` / `kpsewhich fontspec.sty`,
fixed argument lists, no shell=True.

Exit codes: 0 = xelatex + biber + fontspec all found, 1 = something
missing (each item named, plus the install command for this platform).

Usage:
    python check_toolchain.py
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
    "Windows": "winget install --id MiKTeX.MiKTeX -e   (or run install_toolchain.ps1)",
    "Darwin": "brew install --cask mactex-no-gui   (or run install_toolchain.sh)",
    "Linux": "sudo apt-get install -y texlive-xetex texlive-lang-vietnamese biber   (or run install_toolchain.sh)",
}


def check_binary(name: str) -> tuple[bool, str]:
    path = shutil.which(name)
    if not path:
        return False, f"{name} not found on PATH"
    try:
        result = subprocess.run([name, "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10)
        version_line = (result.stdout or result.stderr).splitlines()[0] if (result.stdout or result.stderr) else "unknown version"
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, f"{name} found at {path} but failed to run: {exc}"
    return True, f"{name}: {path} ({version_line})"


def check_fontspec() -> tuple[bool, str]:
    kpsewhich = shutil.which("kpsewhich")
    if not kpsewhich:
        return False, "kpsewhich not found (usually ships with the TeX distro) -- cannot verify fontspec.sty"
    try:
        result = subprocess.run(["kpsewhich", "fontspec.sty"], capture_output=True, text=True, encoding="utf-8", timeout=10)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, f"kpsewhich failed to run: {exc}"
    if result.returncode == 0 and result.stdout.strip():
        return True, f"fontspec.sty: {result.stdout.strip()}"
    return False, "fontspec.sty not found by kpsewhich -- MiKTeX normally installs this on-the-fly on first use; TeX Live may need texlive-xetex explicitly"


def main() -> int:
    checks = [
        ("xelatex", *check_binary("xelatex")),
        ("biber", *check_binary("biber")),
        ("fontspec", *check_fontspec()),
    ]

    all_ok = True
    for name, ok, detail in checks:
        status = "OK" if ok else "MISSING"
        print(f"[{status}] {detail}")
        all_ok = all_ok and ok

    if all_ok:
        print("\nOK: XeLaTeX toolchain ready. latex-project-bootstrap can build.")
        return 0

    system = platform.system()
    hint = INSTALL_HINTS.get(system, "no known install hint for this platform -- install XeLaTeX/biber manually")
    print(f"\nMISSING one or more components. Suggested install ({system}): {hint}", file=sys.stderr)
    print("Nothing was installed by this script -- detection only.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
