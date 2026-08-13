#!/usr/bin/env python3
"""Detect whether the `playwright` Python package and a Chromium browser
binary are available in the shared venv. Read-only -- never installs
anything itself; that's install_browser.ps1/.sh, run only when explicitly
asked (downloads the playwright package + a ~300MB Chromium binary).

Exit codes: 0 = playwright package + Chromium browser both usable,
1 = something missing (reason printed, nothing installed by this script).

Usage:
    .venv/bin/python skills/general/browser-web-renderer/scripts/check_browser.py
"""
from __future__ import annotations

import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[MISSING] playwright package not importable in this venv.", file=sys.stderr)
        print(
            "Suggested install: bash skills/general/toolchain-bootstrap/scripts/bootstrap.sh "
            "skills/general/browser-web-renderer/requirements.txt   (or run install_browser.ps1/.sh)",
            file=sys.stderr,
        )
        return 1

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            version = browser.version
            browser.close()
    except Exception as exc:
        print(f"[MISSING] playwright package found, but Chromium browser binary is not usable: {exc}", file=sys.stderr)
        print(
            "Suggested install: <venv>/bin/python -m playwright install chromium   "
            "(or run install_browser.ps1/.sh)",
            file=sys.stderr,
        )
        return 1

    print(f"[OK] playwright package importable; Chromium browser launches (version: {version})")
    print("Nothing was installed by this script -- detection only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
