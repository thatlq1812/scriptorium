---
name: browser-web-renderer
description: 'Renders a URL with a real headless Chromium browser (Playwright) and extracts its visible text — for JS-rendered SPA pages a plain HTTP fetch can''t read. Two-step like every bootstrap skill in this repo — check_browser.py detects whether playwright + a Chromium binary are ready (safe, default), install_browser.ps1/.sh installs them only when explicitly run (heavy: ~300MB download). render_and_extract.py is read-only: navigates and extracts text, never submits a form, never runs caller-supplied JavaScript, never authenticates, never attempts to evade a site''s bot-detection/WAF. Use when a page is confirmed JS-rendered (not merely slow) and a direct fetch tool already failed to get real content. Do NOT use this as a general scraper for sites that actively block automated access (see the real dichvucong.gov.vn finding below) — rendering the DOM is this skill''s job; getting past a WAF/anti-bot block is a different, out-of-scope problem this project does not attempt to solve by evasion.'
license: MIT
compatibility: 'Requires Python 3.11+, the `playwright` package (via `toolchain-bootstrap`''s shared venv) + a Chromium binary (`playwright install chromium`, ~300MB, downloaded separately from the pip package). Verified running clean: Claude Code, Windows (2026-07-27). See "Verified" section below for real test-case detail.'
metadata:
  domain: general
  task_type: document-conversion
  risk_tier: N2
  source: self-authored
  elicited_from: "Proposed by another agent via request.md (2026-07-27) as a foundation-tier infra skill to close legal-web-search's dichvucong.gov.vn JS-rendering gap. Reviewed before building: flagged as a heavier lift than the prior bootstrap skills (real ~300MB binary download, not a 1-line winget/apt call) and flagged that it might not solve thuvienphapluat.vn's HTTP 403 if that's bot-blocking rather than JS-rendering. Owner approved a 2-step plan: static code first (safe), then explicit approval for the real install + real test. Both approved same session ('Phê duyệt chính thức cho Dev Agent tải Playwright + browser binary... test render DOM thật'). Real testing then found the flagged risk was correct and worse than assumed: dichvucong.gov.vn blocks even a real headless browser at the WAF level, on every page tested including the homepage -- not solvable by rendering alone."
  version: 0.1.0
  grounding: not_applicable
  object_type: []
---

# browser-web-renderer

Renders a URL with a real Chromium browser and extracts its text — the actual fix for a page that returns a JS shell to a plain HTTP fetch (`WebFetch`, `urllib`, etc.), which `legal-web-search` hit for real against `dichvucong.gov.vn` earlier this session.

## Detect (safe, always run first)

```bash
.venv/bin/python skills/general/browser-web-renderer/scripts/check_browser.py
# Windows: .venv\Scripts\python.exe skills\general\browser-web-renderer\scripts\check_browser.py
```

Read-only — tries to import `playwright` and launch Chromium, reports OK/MISSING with the real version when found. Exit 0 = ready. Exit 1 = missing, prints the install command, installs nothing itself.

## Install (heavy — only run after detect shows it's missing)

```bash
# Windows (real PowerShell, not Git Bash -- same uv platform-detection caveat toolchain-bootstrap documents):
.\skills\general\browser-web-renderer\scripts\install_browser.ps1
# macOS/Linux:
bash skills/general/browser-web-renderer/scripts/install_browser.sh
```

Installs the `playwright` package into the shared venv (via `toolchain-bootstrap`), then downloads the Chromium binary (~300MB, separate from the pip package) via `python -m playwright install chromium`. This is a real network download — never run without confirming via `check_browser.py` first that something is actually missing.

## Render and extract

```bash
.venv/bin/python skills/general/browser-web-renderer/scripts/render_and_extract.py <url> [-o output.json] [--screenshot path.png] [--timeout-ms 15000]
```

Navigates to `<url>`, waits for network idle, extracts `document.title` and the full visible body text (`page.inner_text("body")`), optionally saves a full-page screenshot as grounding evidence (proof of what was actually seen, not just claimed). Exit 0 = rendered, output JSON has `url`/`title`/`rendered_at`/`html_length`/`text_content`/`screenshot_path`. Exit 1 = navigation/render failed (timeout, DNS, or — as found for real against `dichvucong.gov.vn` — a WAF block page rendered instead of the real content; check `text_content` even on exit 0, a "Request Rejected" page is technically a successful render of the wrong content). Exit 2 = malformed URL.

## What this skill does NOT do

- **Does not attempt to evade a site's bot-detection/WAF.** `dichvucong.gov.vn` blocked this skill's real headless browser on every page tested (including the bare homepage) with a "Request Rejected" WAF response — this is not a rendering problem headless automation fixes. Spoofing headers/user-agent or otherwise disguising the browser to get past a government site's security control is deliberately out of scope for this project — a different category of action than reading a public page, and not something built here regardless of how useful the data would be.
- Does not submit forms, click through multi-step flows, or execute caller-supplied JavaScript — read-only navigation + text/screenshot extraction only.
- Does not authenticate to anything — `WebFetch`'s own documentation already warns authenticated/private URLs need a different tool; this skill doesn't change that.
- Does not install anything on its own initiative — `check_browser.py` never calls the install scripts.
- Does not replace `legal-web-search`'s domain allowlist/grounding discipline — a caller using this skill's output inside a `legal-web-search` record still needs to follow that skill's rules (dated, allowlisted, disclosed status).

## Verified

Real install (playwright 1.61.0 + Chromium 149.0.7827.55 via uv into the shared venv), `check_browser.py` correctly detects both. `render_and_extract.py` verified real against 2 sites: `vanban.chinhphu.vn` rendered cleanly (2865 chars extracted, richer than a plain WebFetch got earlier the same session — found a real attached PDF link `30.signed.pdf` that WebFetch's summary missed); `dichvucong.gov.vn` was tested on 2 URLs (a procedure page and the bare homepage) and BOTH returned a WAF "Request Rejected" block (124 chars, a rejection page with a support ID) — not a JS-rendering problem, a bot-detection block at the network/WAF layer that a plain headless browser does not get past. This project does not attempt to evade it (see "What this skill does NOT do").

## Known limitations (v0.1.0, not yet through official quality-eval)

- **`dichvucong.gov.vn` remains genuinely unsolved** — confirmed WAF-blocked at the browser level, not just the plain-fetch level. This is now known to be a *different and harder* problem than "JS-rendered," and this project does not plan to solve it by evasion. `legal-web-search`'s Item 4 (form suggestion) Open Gap stays open; the `js_shell_detected`/`snippet_note` short-term mitigation (WebSearch-summary-level, honestly disclosed) remains the practical path for that specific site, not this skill.
- `render_and_extract.py`'s text extraction is whole-page (`body` inner text) — no per-section/selector targeting yet; a caller needing a specific part of a long page gets everything and must parse it themselves.
- No retry/backoff logic — a transient network failure or a slow-loading page beyond `--timeout-ms` fails the whole call, once.
- Verified against exactly 2 real sites this session (`vanban.chinhphu.vn` success, `dichvucong.gov.vn` WAF-blocked) — not yet exercised broadly.
- Hasn't passed stage 4 (quality eval, ≥2 harnesses) or stage 5 (security audit — self-audited only this session: playwright itself is a well-known Microsoft-maintained automation library (Apache-2.0, scouted via `scout-harvester` before building — 14.8k stars, actively maintained); this skill's own 3 scripts add no eval/exec/subprocess/os.system beyond what playwright's own API does internally).
