---
name: gpt-generator
description: 'NOT YET BUILT -- scaffold only, do not use for real work (see Known limitations). Planned: a media-generation toolkit using OpenAI (image/video/audio) via the user''s OWN API key -- BYOK, optional, not an AI backend managed by Scriptorium, same shape as this registry''s `gemini-generator`. Intended coverage: IMAGE generation, VIDEO generation, and AUDIO (TTS) generation through OpenAI''s API. Do NOT use until this skill has real scripts, real API-surface verification, and a version bump documenting that -- currently this is a planning skeleton only.'
license: MIT
compatibility: 'Not yet verified on any harness -- no script exists yet. Will require Python 3.11+, the OpenAI SDK, and the user''s own OpenAI API key, mirroring gemini-generator''s bootstrap shape once built.'
metadata:
  domain: media
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "thatlq1812 (2026-08-13): part of a provider-restructuring of this registry's media generators -- one generator skill per provider (gemini-generator done same day; gpt-generator/claude-generator/normal-generator scaffolded only, real build explicitly deferred to a later session pending real research + an available OpenAI API key for testing -- thatlq1812's own words: '2 cái kia dựng khung sẵn và nói về trước thôi, rồi ta thu thập và dựng hoàn chỉnh gemini-generator nhé' / 'chưa có, x​ây trước chưa test'). No real elicitation source consulted yet for OpenAI's current image/video/audio API surface -- this file deliberately does NOT assert specific model names, endpoints, or capabilities as fact, since this project's own discipline (CLAUDE.md: 'a factual claim without a real, citable source is treated as a bug') applies to a skill's own documentation, not just its runtime output. gemini-generator (this registry's real, fully-built sibling) is the intended structural template once real research happens: one skill_id, one router SKILL.md, per-modality scripts in one scripts/ folder."
  version: 0.0.0
  grounding: not_applicable
  object_type: []
---

# gpt-generator

**Status: scaffold only, not yet implemented.** This file documents planned scope and the reasoning behind it — it is not a working skill. No script exists under `scripts/` yet.

## Planned scope

A BYOK (bring-your-own-key) media-generation toolkit using OpenAI's API, covering the same 3 modalities as this registry's `gemini-generator` (image, video, audio), structured the same way: one skill_id, one router `SKILL.md`, per-modality scripts in one shared `scripts/` folder. Same "doesn't contradict the no-AI-backend principle" reasoning as `gemini-generator` applies here too — the calling agent uses the end user's own OpenAI credentials, Scriptorium never issues or manages the key.

## Why this isn't built yet

Before real scripts get written, this skill needs the same grounding discipline every other skill in this registry follows (`CLAUDE.md` principle 4, general-capability tier — public API documentation is sufficient grounding, no expert interview needed, but it must be *real*, not assumed from stale training knowledge): a direct check of OpenAI's current image/video/audio generation API surface (real endpoint names, real request/response shapes, real model names and their actual constraints — `gemini-generator`'s own build found real, non-obvious API constraints this way, e.g. Veo's `duration_seconds` being a discrete set despite the error text implying a range, and Gemini TTS returning raw unwrapped PCM instead of a playable WAV). None of that verification has happened for OpenAI yet in this session. Real API-call testing additionally needs a real OpenAI API key, which was not available in this environment as of this scaffold's creation (2026-08-13) — flagged honestly per thatlq1812 direction rather than built and left silently unverified.

## What building this for real will need (next steps, not done here)

1. Real research pass: OpenAI's current image generation API (model name, request/response shape, reference-image/edit support if any), video generation API (availability, access model — public API vs. limited access — and its actual request/response shape), and TTS API (voices, streaming vs. request/response, output format) — verified via direct API documentation and/or a real test call, not recalled from training data that may be stale (this session's own date is 2026-08-13, past this assistant's knowledge cutoff).
2. A design decision on whether OpenAI's actual capability shape maps cleanly onto `gemini-generator`'s existing CLI/flag conventions (e.g. `--identity-ref`/`--style-ref`, `--motion-intensity`) or needs its own vocabulary — do not force-fit if the underlying API doesn't support an equivalent capability.
3. Real script implementation + real API-call verification (same bar `gemini-generator` met: real generated output inspected, real error/edge-case paths exercised) before this skill is considered built, before a registry `security_audit`/`quality_score` entry claims anything, and before `operational_status` moves off `planned`.

## What this skill does NOT do (yet)

- Does not generate anything — no working script exists.
- Does not assert any specific OpenAI model name, endpoint, or capability as verified fact — see "Why this isn't built yet" above.
- Is not registered as exportable — `security_audit.status: "pending"` and `operational_status.state: "planned"` both hard-exclude it from `skill-exporter` bundles, same posture as a paused or superseded skill.

## Known limitations (v0.0.0)

Everything. This is a scaffold, not a skill — see "Planned scope" and "What building this for real will need" above for the concrete gap list.
