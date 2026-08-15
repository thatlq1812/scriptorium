---
name: landing-page-composer
description: Drafts a real, scrollable, multi-section HTML/CSS landing page from content you already have (headline, features, testimonial, pricing, CTA, footer text) plus a design system (color tokens + font pairing -- chains directly from `design-system-recommender`'s output). Renders via real headless Chromium (Playwright), the same engine `html-poster-composer` already uses and this project has audited. The raw .html file is the primary deliverable -- open it directly in a browser or hand it to a developer; an optional full-page PNG preview is available for a quick visual check. Use when someone needs to go from raw content to a real webpage draft fast, not when deep custom interactivity/backend logic is needed (that's a developer's job, this produces a static draft). Do NOT use this expecting a full website (multi-page navigation, forms that submit, a CMS) -- one page, static, 6 section types, by design.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only for validation (json, re); rendering the optional PNG preview additionally requires the ''playwright'' package + a Chromium binary (shared with html-poster-composer/browser-web-renderer, bootstrap via browser-web-renderer''s check_browser.py/install_browser.ps1|sh). The .html output itself needs no dependency beyond stdlib. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: webpage
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "thatlq1812 (2026-08-15): direct instruction after reviewing a real, verified 116,839-star repo (nextlevelbuilder/ui-ux-pro-max-skill) -- 'đa số người dùng phổ thông thích dự và phác thảo trang web dựa trên tài liệu họ có trong một thời gian rất ngắn, còn nếu nghĩ tới backend sâu thì họ sẽ không tự làm' (most non-technical users want to quickly draft a webpage from content they already have; they won't attempt deep backend work themselves) -- the explicit design brief this skill's scope follows: fast, real HTML draft output, 6 common section types, no attempt at app/backend functionality. First skill in the new `webpage` domain. Rendering engine directly reuses the real, already-audited HTML/CSS-via-headless-Chromium pattern `html-poster-composer` established (2026-08-07 migration decision, docs/ROADMAP.md) -- same sync_playwright()/chromium.launch()/page.screenshot() mechanism, simplified because a webpage naturally flows/wraps (no fixed-canvas auto-fit-shrink loop needed the way a print poster requires). Section-type vocabulary and the 'first section is always hero' rule are grounded in design-system-recommender's harvested landing_patterns.json (34/34 real patterns from nextlevelbuilder/ui-ux-pro-max-skill start with a hero section, references/PROVENANCE.md in that skill)."
  version: 0.1.0
  grounding: required
  object_type: ["landing-page", "webpage-draft"]
---

# landing-page-composer

Drafts a real, scrollable HTML/CSS landing page from content + a design system. The .html file is the deliverable; the PNG is a quick visual check.

## Why this skill, and why this scope

thatlq1812 directed building this after reviewing a real, verified 116,839-star repository, with an explicit design brief: most non-technical users want a fast webpage *draft* from content they already have, not a deep custom app -- that's a developer's job. This skill is deliberately scoped to match: one page, 6 common section types (covering the section vocabulary that recurs across the vast majority of the harvested 34 real landing-page patterns), static HTML/CSS output, no forms-that-submit, no multi-page navigation, no CMS. It reuses `html-poster-composer`'s already-proven, already-audited HTML/CSS-via-headless-Chromium rendering pattern rather than inventing a new one.

## What this skill does

1. **Validates structure** (`scripts/validate_content.py`): `design_system.color_tokens` must declare all 16 semantic tokens as valid hex colors; `design_system.font_pairing` needs non-empty `heading_font`/`body_font`; `sections` must be non-empty, its first entry must be `type: "hero"` (a real, 34/34-corroborated convention, not an arbitrary rule), and every section's type-specific required fields must be present (see below).
2. **Composes real HTML/CSS** (`scripts/compose.py`): binds the design system to CSS custom properties, renders each section to semantic HTML, writes a real `.html` file you can open directly in any browser.
3. **Optional PNG preview** (`--png`): renders the composed page through headless Chromium for a full-page screenshot, so you can eyeball it without opening a browser yourself.

### The 6 section types

| Type | Required fields |
| --- | --- |
| `hero` | `headline`, `cta_text`, `cta_href` (`subheadline` optional) |
| `features` | `title`, `items` (list of `{title, description}`, ≥1) |
| `testimonial` | `quote`, `author` (`role` optional) |
| `pricing` | `tiers` (list of `{name, price, features: [...]}`, ≥1) |
| `cta` | `headline`, `button_text`, `button_href` |
| `footer` | `text` (`links` optional, list of `{label, href}`) |

## Run

```bash
python scripts/compose.py <content.json> -o page.html [--png preview.png] [--width 1440]
```

Start from `assets/landing_page_template.json` (a full 6-section example using a real harvested design system). `compose.py` validates before touching Playwright -- an invalid `content.json` refuses (exit 1) with no file written, same discipline `html-poster-composer` already established. `--png` is optional; omit it to get just the `.html` with zero Playwright/Chromium dependency.

## Chains from `design-system-recommender`

Run that skill first (`python scripts/recommend_design_system.py --product-type "..."`), then map its output into this skill's `design_system` input: its `color_tokens` maps directly (same 16 keys); its `font_pairing.heading_font`/`body_font`/`google_fonts_url` maps directly too. The bundled template already demonstrates this exact pairing (SaaS design system + Poppins/Open Sans).

## What this skill does NOT do

- Does not build a full website -- one page, no routing/navigation between pages, no CMS, no backend.
- Does not make forms actually submit anywhere -- a `cta_href`/`button_href` is a plain link, wiring it to a real form handler is a developer's job.
- Does not invent section content -- every field is caller-supplied; this skill structures and renders it, never writes marketing copy for you.
- Does not guarantee WCAG contrast for a specific real combination beyond what the design system's own source curation already accounted for (see `design-system-recommender`'s own scope note).
- Does not support section types beyond the 6 listed -- the harvested pattern data covers many more real archetypes (video-first hero, comparison tables, 3D configurators...); a future version could add more, flagged as a real, deliberate v0.1.0 scope limit, not an oversight.
- Does not call any LLM/AI API for the composition itself -- pure template rendering; Playwright is used only as a real browser to take a screenshot, not for any AI purpose.

## Verified

The bundled template (6 sections, a real harvested SaaS design system with Poppins/Open Sans) renders correctly -- verified by direct visual inspection of the rendered PNG, which caught and led to fixing a real bug: declaring a Google Font by name in CSS alone does NOT load it without an actual `<link>` to fonts.googleapis.com, so the first render silently fell back to a generic sans-serif with zero warning; fixed by injecting the real `<link>` when `google_fonts_url` is given, re-verified the heading font visibly changed in the corrected render. A deliberately broken record (an invalid hex color, several missing color tokens, an empty `heading_font`, a `features` section placed first instead of `hero`, an unrecognized section type, and a `hero` section missing `headline`/`cta_href`) correctly caught all 21 issues in one run, and `compose.py` correctly refused to touch Playwright at all when validation failed (no file written). A record missing both required top-level keys and malformed JSON both correctly refused/flagged.

## Known limitations (v0.1.0, not yet through official quality-eval)

- Only 6 of the many real landing-page section archetypes in the harvested pattern data are implemented -- flagged as a real, deliberate scope limit (see "What this skill does NOT do"), matching this project's own precedent (`slide-deck-composer` similarly ported 6 of ~20 source layout types first).
- No responsive breakpoint tuning beyond CSS Grid's own `auto-fit`/`minmax` behavior -- not tested against real mobile-viewport rendering this session, only the default desktop-width preview.
- Does not validate that a `cta_href`/`button_href`/link `href` is a real, resolvable URL -- any non-empty string passes.
- Only verified against hand-authored fixtures this session, not yet exercised against a real user's actual raw content (a real "document they have" turned into a real draft).
