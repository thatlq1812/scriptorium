---
name: ui-icon-recommender
description: A curated LOOKUP tool, never a generator. Given an icon need (exact name, free-text keywords, or a UI category like "Navigation"/"Action"/"Commerce"), deterministically returns real Phosphor icon(s) -- the exact React import statement and, critically, the correct accessibility treatment (whether the icon is decorative/meaningful/interactive and what aria handling each requires) -- from a bundled, curated 105-icon reference. Use when drafting a UI and need a specific, real icon plus how to make it accessible, instead of guessing an icon name or forgetting aria handling. Do NOT use this expecting a full icon library (only 105 curated icons, not the full ~1,500+ real Phosphor set) or an AI-generated/custom icon.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) -- no dependency, no venv needed, zero network calls of any kind. Verified running clean: Claude Code (2026-08-15).'
metadata:
  domain: design
  task_type: research
  risk_tier: N1
  source: harvested
  elicited_from: "Harvested from the same source as design-system-recommender/ui-style-guide-lookup (nextlevelbuilder/ui-ux-pro-max-skill, verified 116,839 stars via gh api, MIT, same source commit a38d04c3d5c298c851dbe5e6ee1965ee3de42cb5, full provenance in that skill's references/PROVENANCE.md) -- adapts icons.csv (105 rows). Part of the broader harvest thatlq1812 directed after pushing back on an initially narrow 2-skill/1-webpage-domain-skill extraction ('cả cái repo đó bạn trích ra được mỗi 2 skill... cần rộng hơn')."
  version: 0.1.0
  grounding: required
  object_type: ["icon", "accessibility-role"]
---

# ui-icon-recommender

Looks up a real, curated icon by name/keyword/category, including the correct accessibility treatment. Never generates or invents an icon.

## Why this skill, and why this scope

Icon selection is a small but real, recurring need when drafting any UI (buttons, navigation, status indicators) -- and getting the accessibility treatment wrong (an icon-only button with no accessible name, or a decorative icon read aloud by a screen reader) is a real, common defect. This skill's source data curates both the icon itself and its correct `decorative`/`meaningful`/`interactive` role handling together, which is the actual value beyond "just search an icon library."

## What this skill does

1. **Exact lookup** (`--icon-name arrow-left`): returns the full entry.
2. **Fuzzy lookup** (`--keywords "delete remove trash"`, `--max-results N`): returns up to N candidates ranked by keyword overlap, with the match count disclosed to stderr.
3. **Category browse** (`--category Navigation`): returns every icon in that exact category. `--list-categories` shows all 18 real categories (Action, Commerce, Communication, Data, Development, Device, Files, Guideline, Layout, Location, Media, Navigation, Security, Social, Status, Style Config, Time, User).
4. Every result includes the real `import_code` (React/Phosphor), `style` (Outline/Fill/etc.), `semantic_role`, and `allowed_contexts` -- the accessibility-role guidance.

## Run

```bash
python scripts/recommend_icon.py --icon-name arrow-left
python scripts/recommend_icon.py --keywords "delete remove trash"
python scripts/recommend_icon.py --category Navigation
python scripts/recommend_icon.py --list-categories
```

`-o/--output <path>` writes the result JSON to a file. Exit 0 = match found, 1 = no match, 2 = malformed input/missing args.

## What this skill does NOT do

- Does not generate or design a custom icon -- every result is a real, pre-existing entry from a 105-icon curated subset, not the full Phosphor library (~1,500+ real icons) and never AI-generated.
- Does not verify the icon is actually correctly implemented with the recommended accessibility attributes in your real codebase -- it recommends the pattern, applying it correctly is the caller's job.
- Does not call any LLM/AI API -- pure stdlib lookup/scoring.

## Verified

Data integrity verified during harvest: all 105 icons have non-empty `icon_name` and `import_code`. Script-tested for real: exact `--icon-name` lookup returns the full structure; `--keywords` fuzzy match returns ranked candidates with disclosed scores; `--category Navigation` returns all matching icons (8 found); `--list-categories` prints all 18 real categories; a nonexistent icon name and missing-args case both correctly refuse (exit 1 / exit 2).

## Known limitations (v0.1.0, not yet through official quality-eval)

- Only 105 curated icons, not the full real Phosphor library -- a real, disclosed coverage gap, not silently papered over with a near-miss recommendation.
- Keyword matching is exact-token-overlap only, no stemming/synonym expansion.
- Only verified against the full bundled dataset's own internal consistency this session, not yet exercised as part of a real UI-drafting task.
