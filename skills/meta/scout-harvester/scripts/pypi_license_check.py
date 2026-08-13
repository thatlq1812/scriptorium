#!/usr/bin/env python3
"""Quick PyPI package license lookup via the public JSON API — wraps the
`curl https://pypi.org/pypi/<pkg>/json` pattern used repeatedly this session
(google-genai, python-docx, python-pptx, openpyxl, pypdfium2). Stdlib only
(urllib), no dependency.

Usage:
    python pypi_license_check.py google-genai
    python pypi_license_check.py python-docx python-pptx openpyxl  # multiple at once
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

PYPI_URL = "https://pypi.org/pypi/{package}/json"


def check_package(package: str) -> dict:
    url = PYPI_URL.format(package=package)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"package": package, "error": f"HTTP {exc.code} — package not found on PyPI"}
    except urllib.error.URLError as exc:
        return {"package": package, "error": f"Network error: {exc.reason}"}

    info = data.get("info", {})
    license_field = info.get("license") or None
    license_expression = info.get("license_expression") or None
    # PyPI's classic `license` field is free text and often empty; newer
    # packages set `license_expression` (SPDX) via PEP 639. Prefer the SPDX
    # expression, fall back to classifiers, then the free-text field.
    classifiers = [c for c in info.get("classifiers", []) if c.startswith("License ::")]
    resolved = license_expression or license_field or (classifiers[0] if classifiers else None)

    return {
        "package": package,
        "version": info.get("version"),
        "license_expression": license_expression,
        "license_field": license_field,
        "license_classifiers": classifiers,
        "resolved": resolved,
        "home_page": info.get("home_page") or info.get("project_url"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("packages", nargs="+")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a table")
    args = parser.parse_args()

    results = [check_package(p) for p in args.packages]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if "error" in r:
                print(f"{r['package']}: ERROR — {r['error']}")
                continue
            print(f"{r['package']} {r['version']}: resolved license = {r['resolved']}")
            if r["license_field"] and r["license_field"] != r["resolved"]:
                print(f"  (raw license field: {r['license_field']!r})")

    print(
        "\nReminder: this resolves what PyPI/the package publisher DECLARES. "
        "Cross-check against the actual repo's LICENSE file before harvesting code, "
        "not just this metadata — see license-compliance-check's rule on always "
        "reading the license at the most specific level available.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
