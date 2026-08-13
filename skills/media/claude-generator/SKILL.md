---
name: claude-generator
description: 'NOT YET BUILT -- scaffold only, do not use for real work (see Known limitations). Planned: a generation toolkit using Claude (Anthropic API) via the user''s OWN API key -- BYOK, optional, not an AI backend managed by Scriptorium. Unlike gemini-generator/gpt-generator (pixel-based image/video), this targets Claude''s real strength: CODE, SVG, and structured DOCUMENT generation -- Claude has no native pixel-image/video generation API, so this skill deliberately does not attempt to fake one. Do NOT use until this skill has real scripts and real API-surface verification -- currently a planning skeleton only.'
license: MIT
compatibility: 'Not yet verified on any harness -- no script exists yet. Will require Python 3.11+, the Anthropic SDK, and the user''s own Anthropic API key.'
metadata:
  domain: media
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Owner (2026-08-13): part of the same provider-restructuring as gpt-generator/normal-generator (see gemini-generator, the one fully-built sibling, for the real template this will follow structurally). Owner explicitly confirmed this skill's real scope when asked directly, since Claude has no native image/video generation API the way Gemini (Imagen/Veo) or OpenAI (DALL-E/Sora) do: 'Sinh code/SVG/tài liệu qua Claude' (generate code/SVG/documents via Claude) -- i.e. this skill targets Claude's real, verifiable strength (structured text/code/markup generation via the Messages API) rather than force-fitting a pixel-generation shape Claude's API doesn't actually offer. Scaffolded only this round, real build deferred pending an available Anthropic API key for testing and a concrete design decision on scope overlap with this registry's existing code/document-shaped skills (see 'Why this isn't built yet')."
  version: 0.0.0
  grounding: not_applicable
  object_type: []
---

# claude-generator

**Status: scaffold only, not yet implemented.** This file documents planned scope and the reasoning behind it — it is not a working skill. No script exists under `scripts/` yet.

## Planned scope

A BYOK (bring-your-own-key) generation toolkit using Claude's real Messages API, producing **code, SVG, and structured documents** — not pixel-based image/video, which Claude's API doesn't offer (unlike Gemini's Imagen/Veo or OpenAI's DALL-E/Sora). Same "doesn't contradict the no-AI-backend principle" reasoning as `gemini-generator`: the calling agent uses the end user's own Anthropic credentials, Scriptorium never issues or manages the key.

## Why this isn't built yet

Two real gaps before this becomes a working skill, not just a naming placeholder:

1. **No real API-key testing available yet** (2026-08-13) — same honesty bar `gemini-generator`'s own voice-cloning feature was held to when it couldn't be tested (flagged as unverified rather than claimed working).
2. **A real scope-overlap question not yet resolved**: this registry already has skills that generate SVG (`light-logo-arranger`, `html-poster-composer`'s underlying render pipeline) and structured documents (`office-doc-creator`, `document-ai-structurer`, `slide-deck-composer`) — none of which currently call an AI backend themselves (per `CLAUDE.md` principle 8, they're deterministic renderers driven by caller-supplied content). `claude-generator`'s actual value proposition needs to be concretely different from those — e.g. "call Claude's own API to *draft* the content/structure a deterministic renderer then executes," not a duplicate SVG/document renderer. This distinction needs to be nailed down with a real use case before scripts get written, not assumed.

## What building this for real will need (next steps, not done here)

1. A concrete real use case naming exactly what Claude-generated code/SVG/document artifact is needed that isn't already covered by an existing deterministic Scriptorium skill — avoiding a near-duplicate (this registry's own dedup-novelty discipline, `registry/SCHEMA.md`).
2. Real Anthropic Messages API verification (current model names, real request/response shape for the intended use — e.g. structured output via tool-use/JSON mode if the use case needs machine-parseable output) — verified directly, not recalled from training data that may be stale relative to this session's date (2026-08-13).
3. Real script implementation + real API-call verification before `operational_status` moves off `planned`.

## What this skill does NOT do (yet)

- Does not generate anything — no working script exists.
- Does not generate pixel-based images or video — Claude's API has no native capability for either; see `gemini-generator`/`gpt-generator` for that.
- Does not assert any specific Claude model name or API capability as verified fact.
- Is not registered as exportable — `security_audit.status: "pending"` and `operational_status.state: "planned"` both hard-exclude it from `skill-exporter` bundles.

## Known limitations (v0.0.0)

Everything. This is a scaffold, not a skill — see "Planned scope" and "What building this for real will need" above for the concrete gap list.
