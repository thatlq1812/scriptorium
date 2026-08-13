---
name: normal-generator
description: 'NOT YET BUILT -- scaffold only, do not use for real work (see Known limitations). Planned: a PROVIDER-AGNOSTIC generation toolkit -- unlike gemini-generator/gpt-generator/claude-generator (one hardcoded provider each), this is meant to adapt to ANY AI generation provider given its own API docs + the user''s own key, for long-tail/uncommon providers this registry will never build a dedicated skill for. Do NOT use until this skill has a real, tested adapter mechanism -- currently a planning skeleton only, and the actual design is not yet settled (see Known limitations).'
license: MIT
compatibility: 'Not yet verified on any harness -- no script exists yet, and the underlying mechanism design itself is not yet settled.'
metadata:
  domain: media
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "Owner (2026-08-13): part of the same provider-restructuring as gpt-generator/claude-generator. Owner's own description of intent, verbatim reasoning preserved since the exact scope is still being settled: 'có sẵn các thuật toán generator và có thể chủ động đáp ứng với bất kì provider nào, dành cho kiểu antigravity tự gen, hoặc gọi các provider AI lạ, hoặc dùng với các api docs và key không phổ biến ấy' (generator algorithms ready, able to proactively adapt to ANY provider -- for the 'antigravity self-gen' style, or calling unusual/uncommon AI providers, or working with uncommon API docs and keys). Owner separately pointed at D:/elix/platform (Elixverse, the owner's own real production multi-provider LLM router) as a reference to consult. Investigated directly (2026-08-13, via a research agent reading the real code at D:/elix/platform/server/src/core/ai/): confirmed Elixverse itself does NOT have a generic 'any provider via docs' mechanism -- it uses a `BaseAIAdapter` interface (adapters/base.py) with one hand-written concrete adapter class per provider (gemini_adapter.py/openai_adapter.py/anthropic_adapter.py), each directly using that provider's own official SDK and manually translating a shared Message/ContentBlock shape into that provider's native request format; routing (router.py: AIRouter) is a 3-step waterfall (explicit model pin -> admin-configured DB default -> hardcoded fallback chains). This is a real, load-bearing finding: normal-generator's 'adapt to any provider' goal has NO direct real precedent even in the owner's own most relevant production system -- every real adapter Elixverse has was still hand-written per-provider, not generated from arbitrary docs. This skill's actual design therefore needs to be resolved as its own open question (see 'Why this isn't built yet'), not assumed solved by copying an existing pattern."
  version: 0.0.0
  grounding: not_applicable
  object_type: []
---

# normal-generator

**Status: scaffold only, not yet implemented, design not yet settled.** This file documents the planning question this skill needs to answer before any script gets written — it is not a working skill.

## Planned scope (as currently understood)

A provider-agnostic generation toolkit — unlike `gemini-generator`/`gpt-generator`/`claude-generator` (one specific, hardcoded provider each), this is meant to help a caller reach an AI generation provider **this registry has no dedicated skill for**: a niche/long-tail provider, a self-hosted model endpoint, or a provider the owner has access to via API docs and a key but that isn't common enough to justify its own skill. Owner's own framing names 3 real use cases: (1) an "antigravity-style self-gen" pattern (a caller improvising a call from docs rather than a pre-built integration), (2) calling an uncommon/unusual AI provider, (3) working with uncommon API docs + keys generally.

## Why this isn't built yet

The real, load-bearing finding from checking the owner's own Elixverse codebase (see `metadata.elicited_from`): **there is no existing real precedent for a generic "any provider, given only docs" adapter, even in the owner's own most relevant production system.** Elixverse's own multi-provider router hand-writes one concrete adapter class per provider — it does not synthesize an adapter from arbitrary documentation at runtime. This means `normal-generator`'s actual mechanism is a genuinely open design question, not a known pattern to port:

- Does "provider-agnostic" mean this skill ships a **generic HTTP-call construction helper** (the caller supplies an endpoint, auth header shape, and request/response field mapping — filled in by the calling agent reading the target provider's own docs at use-time — and this skill handles the mechanical HTTP call safely: timeout, retry, error surfacing) rather than actually understanding any provider's semantics itself?
- Or does it mean a **caller-declared adapter template** (a JSON/YAML shape describing one provider's request/response mapping, saved and reused across calls, closer to Elixverse's own adapter concept but authored by the calling agent instead of a Scriptorium engineer)?
- Safety surface needs real thought before any script is written: an HTTP call to an arbitrary caller-supplied endpoint is a materially different risk class from `gemini-generator`/`gpt-generator`/`claude-generator`'s fixed, known-safe official endpoints — this needs its own security-audit posture (e.g. refusing non-HTTPS endpoints, never executing caller-supplied code/templates as Python, treating the response as untrusted data), not inherited from the other 3 generator skills' audit notes.

## What building this for real will need (next steps, not done here)

1. An owner decision on which of the two mechanism shapes above (or a third option) this skill actually is, since the two are genuinely different amounts of work and different risk profiles.
2. A concrete real use case (a specific uncommon provider the owner actually wants to call) to design and test against, rather than an abstract "any provider" target with nothing real to verify against.
3. A real security-audit pass scoped to the "arbitrary endpoint" risk surface specifically, before this ships even as v0.1.0.

## What this skill does NOT do (yet)

- Does not generate anything — no working script exists.
- Does not have a settled internal design — see "Why this isn't built yet" above.
- Is not registered as exportable — `security_audit.status: "pending"` and `operational_status.state: "planned"` both hard-exclude it from `skill-exporter` bundles.

## Known limitations (v0.0.0)

Everything, including the mechanism design itself — this is the least-defined of the 4 planned generator skills. See "Why this isn't built yet" for the specific open question blocking any implementation work.
