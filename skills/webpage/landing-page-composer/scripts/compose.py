#!/usr/bin/env python3
"""Composes a real, scrollable HTML/CSS landing-page draft from a
content.json (design_system + ordered sections), then renders a full-page
PNG preview via headless Chromium (Playwright) -- the same real-browser-
rendering engine html-poster-composer already uses and this project has
already audited, applied here to a naturally-flowing multi-section page
instead of a fixed-canvas poster (no auto-fit-shrink loop needed: a
webpage wraps/grows, it doesn't need to fit a fixed print size).

The raw .html file is the primary deliverable (open it directly in a
browser, or hand it to a developer to wire up) -- the .png is a quick
visual check, not the end product.

Usage:
    python compose.py <content.json> -o page.html [--png preview.png] [--width 1440]

Exit 0 = rendered, 1 = content validation failed, 2 = malformed input/args.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_content import validate  # noqa: E402

DEFAULT_VIEWPORT_WIDTH = 1440


def _esc(s: str) -> str:
    return html_lib.escape(s, quote=True)


def _base_css(tokens: dict, heading_font: str, body_font: str) -> str:
    token_vars = "\n".join(f"  --{k.replace('_', '-')}: {v};" for k, v in tokens.items())
    return f"""
:root {{
{token_vars}
  --font-heading: '{_esc(heading_font)}', sans-serif;
  --font-body: '{_esc(body_font)}', sans-serif;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: var(--font-body); color: var(--foreground); background: var(--background); line-height: 1.5; }}
h1, h2, h3 {{ font-family: var(--font-heading); line-height: 1.2; }}
.container {{ max-width: 1120px; margin: 0 auto; padding: 0 24px; }}
.btn {{ display: inline-block; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600;
  background: var(--primary); color: var(--on-primary); border: none; cursor: pointer; }}
.btn-accent {{ background: var(--accent); color: var(--on-accent); }}
section {{ padding: 72px 0; }}
.card {{ background: var(--card); color: var(--card-foreground); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }}
.muted {{ color: var(--muted-foreground); }}
""".strip()


def _render_hero(s: dict) -> str:
    sub = f"<p class='muted' style='font-size:1.25rem;margin-top:16px;'>{_esc(s['subheadline'])}</p>" if s.get("subheadline") else ""
    return f"""
<section class="hero" style="background:var(--background); text-align:center;">
  <div class="container">
    <h1 style="font-size:3rem;">{_esc(s['headline'])}</h1>
    {sub}
    <div style="margin-top:32px;">
      <a class="btn" href="{_esc(s['cta_href'])}">{_esc(s['cta_text'])}</a>
    </div>
  </div>
</section>"""


def _render_features(s: dict) -> str:
    items_html = "\n".join(
        f"<div class='card'><h3>{_esc(it['title'])}</h3><p class='muted' style='margin-top:8px;'>{_esc(it['description'])}</p></div>"
        for it in s["items"]
    )
    return f"""
<section class="features" style="background:var(--muted);">
  <div class="container">
    <h2 style="text-align:center;font-size:2.25rem;margin-bottom:40px;">{_esc(s['title'])}</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px;">
      {items_html}
    </div>
  </div>
</section>"""


def _render_testimonial(s: dict) -> str:
    role = f", {_esc(s['role'])}" if s.get("role") else ""
    return f"""
<section class="testimonial" style="text-align:center;">
  <div class="container" style="max-width:720px;">
    <p style="font-size:1.5rem;font-style:italic;">&ldquo;{_esc(s['quote'])}&rdquo;</p>
    <p class="muted" style="margin-top:16px;font-weight:600;">{_esc(s['author'])}{role}</p>
  </div>
</section>"""


def _render_pricing(s: dict) -> str:
    tiers_html = []
    for tier in s["tiers"]:
        features_html = "".join(f"<li style='margin-top:8px;'>{_esc(f)}</li>" for f in tier["features"])
        tiers_html.append(
            f"<div class='card' style='text-align:center;'><h3>{_esc(tier['name'])}</h3>"
            f"<p style='font-size:2rem;margin:16px 0;'>{_esc(tier['price'])}</p>"
            f"<ul style='list-style:none;text-align:left;'>{features_html}</ul></div>"
        )
    return f"""
<section class="pricing" style="background:var(--muted);">
  <div class="container">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px;">
      {''.join(tiers_html)}
    </div>
  </div>
</section>"""


def _render_cta(s: dict) -> str:
    return f"""
<section class="cta" style="background:var(--primary);color:var(--on-primary);text-align:center;">
  <div class="container">
    <h2 style="font-size:2.25rem;">{_esc(s['headline'])}</h2>
    <div style="margin-top:24px;">
      <a class="btn btn-accent" href="{_esc(s['button_href'])}">{_esc(s['button_text'])}</a>
    </div>
  </div>
</section>"""


def _render_footer(s: dict) -> str:
    links = s.get("links") or []
    links_html = " &middot; ".join(f"<a href='{_esc(l['href'])}' style='color:inherit;'>{_esc(l['label'])}</a>" for l in links)
    links_block = f"<div style='margin-top:12px;'>{links_html}</div>" if links_html else ""
    return f"""
<footer style="background:var(--foreground);color:var(--background);text-align:center;padding:40px 0;">
  <div class="container">
    <p>{_esc(s['text'])}</p>
    {links_block}
  </div>
</footer>"""


RENDERERS = {
    "hero": _render_hero,
    "features": _render_features,
    "testimonial": _render_testimonial,
    "pricing": _render_pricing,
    "cta": _render_cta,
    "footer": _render_footer,
}


def build_html(content: dict) -> str:
    ds = content["design_system"]
    tokens = ds["color_tokens"]
    font = ds["font_pairing"]
    body_parts = [RENDERERS[s["type"]](s) for s in content["sections"]]
    # Declaring a Google Font by family name in CSS alone does NOT load it --
    # without an actual <link>/@import to fonts.googleapis.com, the browser
    # silently falls back to a generic sans-serif with no warning (found for
    # real via visual inspection of the rendered PNG this session: Poppins/
    # Open Sans were declared but the render showed a plain fallback font).
    font_link = ""
    if ds.get("font_pairing", {}).get("google_fonts_url"):
        font_link = f"<link rel='stylesheet' href=\"{_esc(font['google_fonts_url'])}\">"
    return (
        "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"{font_link}"
        f"<style>{_base_css(tokens, font['heading_font'], font['body_font'])}</style></head>"
        f"<body>{''.join(body_parts)}</body></html>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("content_path", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output .html path")
    parser.add_argument("--png", type=Path, help="Also render a full-page PNG preview at this path")
    parser.add_argument("--width", type=int, default=DEFAULT_VIEWPORT_WIDTH, help="Preview viewport width in px")
    args = parser.parse_args()

    try:
        content = json.loads(args.content_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2
    if not isinstance(content, dict):
        print("MALFORMED: input must be a JSON object", file=sys.stderr)
        return 2

    errors = validate(content)
    if errors:
        print(f"INVALID content ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    html_str = build_html(content)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_str, encoding="utf-8")
    print(f"OK: wrote {args.output} ({len(content['sections'])} section(s))")

    if args.png:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            sys.exit(
                "compose.py --png requires the 'playwright' package + a Chromium binary. "
                "Bootstrap via the 'browser-web-renderer' skill's check_browser.py/install_browser.ps1|sh "
                "(shared venv, same dependency this project already installs and audits), or omit --png "
                "to get just the .html file with no rendering."
            )
        args.png.parent.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": args.width, "height": 900})
            page.goto(args.output.resolve().as_uri())
            page.screenshot(path=str(args.png), full_page=True)
            browser.close()
        print(f"OK: wrote {args.png}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
