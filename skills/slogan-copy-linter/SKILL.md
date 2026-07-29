---
name: slogan-copy-linter
description: Structure/tone linter for short marketing copy (slogans, taglines, signboard headlines). `validate_copy.py` checks a slogan against a caller-declared character cap (no built-in default -- the right cap depends on the physical medium), a caller-declared banned-word/phrase list (case-insensitive substring match, e.g. unverifiable superlative claims like "so 1 the gioi"), and warns (non-blocking) on an all-caps ("shouting") slogan unless the caller explicitly declares that's the intended brand style. Use when reviewing draft marketing copy for a signboard, menu, banner, or flyer before finalizing it. Do NOT use this to judge whether a slogan is creatively good -- only the 3 mechanical checks above.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29).
metadata:
  domain: general
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "General-capability tier (CLAUDE.md principle 4) — short-copy length constraints and unverifiable-superlative-claim risk are publicly well-documented marketing/advertising-standards concerns, not a niche tacit process. Companion skill to brand-identity-linter/svg-poster-builder within UPGRADE_PLAN_20260729.md Item 4's Light Design cluster, same real signboard/menu project as grounding context for the fixture's structure (D:/elix/temp_project_20260728) -- fixture text itself is a generic invented example, not the real client's actual slogan."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["marketing-copy"]
---

# slogan-copy-linter

3 mechanical checks: length cap, banned-phrase scan, all-caps warning. Nothing about creative quality.

## Why this skill, and why this scope

A signboard/menu/banner's slogan has a real physical constraint (available print space) that varies by medium — this skill never guesses a universal length cap, the caller always declares `max_chars` for their specific layout. The banned-word check exists for the same reason `legal-citation-checker`/`document-ai-structurer` refuse to fabricate legal claims: an unverifiable superlative ("số 1 thế giới") is a factual claim a business usually can't back up, and flagging it mechanically (caller declares the banned list) is cheaper than catching it after print.

## Run

```bash
python scripts/validate_copy.py <copy.json>
```

Start from `assets/copy_template.json`. Exit 0 = valid (warnings, if any, are non-blocking and still print), 1 = hard violation (all printed), 2 = malformed input.

### Schema

```json
{
  "slogan": "string",
  "max_chars": 20,
  "banned_words": ["string", "..."],
  "allow_all_caps": false
}
```

## What this skill does NOT do

- Does not judge creative/aesthetic quality of a slogan — only length, banned-phrase presence, and the all-caps warning.
- Does not have a built-in length cap — `max_chars` is always caller-declared, since the right cap depends on the physical medium, never guessed.
- Does not do fuzzy/semantic banned-word matching — exact case-insensitive substring match only, same "never guess a match" discipline as every other linter in this registry.

## Verified

The bundled `copy_template.json` passed clean with no warning. 4 deliberately broken/edge cases: a slogan exceeding a declared `max_chars=5` correctly refused with the exact char count; a slogan containing a declared banned phrase ("rẻ nhất") correctly refused, naming the exact phrase; an all-caps slogan correctly produced a non-blocking warning (still exit 0) naming the `allow_all_caps` escape hatch; an empty slogan correctly refused (exit 1).

## Known limitations (v0.1.0)

- Banned-word matching is exact substring, not fuzzy or stemmed — a banned phrase with different spacing/punctuation won't be caught.
- No multi-language-specific tone analysis (e.g. Vietnamese-specific register/politeness checking) — purely mechanical length/banned-phrase/caps checks, language-agnostic.
- Only checks a single slogan per run — no batch mode for a full copy deck yet.
