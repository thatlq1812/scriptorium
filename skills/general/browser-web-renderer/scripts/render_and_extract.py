#!/usr/bin/env python3
"""Render a URL with a real headless Chromium browser (via Playwright) and
extract its visible text content -- for JS-rendered SPA pages a plain HTTP
fetch can't read (confirmed real gap: dichvucong.gov.vn procedure/form
pages return only a JS shell to a direct fetch, see legal-web-search's
Known limitations).

Read-only: navigates and extracts, never submits a form, never executes
caller-supplied JavaScript, never authenticates. Optionally saves a
screenshot as grounding evidence (what was actually seen, not just claimed).

Requires the playwright package + Chromium browser binary already
installed (see check_browser.py / install_browser.ps1/.sh -- this script
does not install anything itself).

Exit codes: 0 = rendered and extracted, 1 = navigation/render failed,
2 = malformed arguments.

Usage:
    python render_and_extract.py <url> [-o output.json] [--screenshot path.png] [--timeout-ms 15000]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url")
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument("--screenshot", type=Path, default=None, help="optional path to save a full-page screenshot as grounding evidence")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    if not args.url.startswith(("http://", "https://")):
        print(f"REFUSED: url must start with http:// or https://, got {args.url!r}", file=sys.stderr)
        return 2

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright package not importable -- run check_browser.py first.", file=sys.stderr)
        return 1

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(args.url, wait_until="networkidle", timeout=args.timeout_ms)
            title = page.title()
            text_content = page.inner_text("body")
            html_length = len(page.content())
            if args.screenshot:
                page.screenshot(path=str(args.screenshot), full_page=True)
            browser.close()
    except Exception as exc:
        print(f"RENDER FAILED: {exc}", file=sys.stderr)
        return 1

    result = {
        "url": args.url,
        "title": title,
        "rendered_at": datetime.now(timezone.utc).isoformat(),
        "html_length": html_length,
        "text_content": text_content,
        "screenshot_path": str(args.screenshot) if args.screenshot else None,
    }

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"OK: rendered {args.url!r} ({len(text_content)} chars extracted) -> {args.output}", file=sys.stderr)
    else:
        print(out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
