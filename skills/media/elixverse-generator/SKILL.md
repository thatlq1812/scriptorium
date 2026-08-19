---
name: elixverse-generator
description: 'PAUSED 2026-08-19 (thatlq1812 decision -- Elixverse platform gap, not a defect in this skill, see Known limitations) -- do not deploy. An image-generation toolkit using Elixverse''s OpenAI-compatible REST API via the user''s OWN Elixverse API key -- BYOK, optional, not an AI backend managed by Scriptorium (same shape as this registry''s gemini-generator). Covers IMAGE generation only for now: single-image generation, independent identity+style anchoring via a text-description bridge (Elixverse''s /images/generations has no native reference-image input), and vision-based reference-image analysis. Use whenever the user has their own Elixverse API key and needs to generate an image, optionally anchored to an existing identity/style reference. Do NOT use if the user lacks their own key -- not a shortcut around the "no AI backend" principle (see the note below).'
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (urllib.request, json, base64, mimetypes -- no SDK/dependency, no venv bootstrap needed) + the user''s own ELIXVERSE_API_KEY. Verified running clean: Claude Code, Windows, real API calls against https://api.elixverse.com/api/v1 (2026-08-19) -- see "Verified" below.'
metadata:
  domain: media
  task_type: drafting
  risk_tier: N2
  source: self-authored
  elicited_from: "thatlq1812 (2026-08-19, PROJECT.md): real Elixverse API quickstart docs pasted directly from Elixverse's own frontend documentation (base URL, auth header, endpoint list, request/response shapes for /chat/completions, /images/generations, streaming, tools, vision, structured output) -- this is the real, citable source for this skill's REST surface, not recalled/assumed knowledge. Cross-verified against Elixverse's actual server-side source at D:/elix/platform/server/src/api/v1/images.py (ImageGenerationRequest pydantic model: prompt/model/size/quality/n/style/response_format, no reference-image field) -- this confirmed the real constraint driving this skill's anchor design (see 'Anchor design' below): no native image-conditioning input exists on this endpoint, so identity/style anchoring goes through a vision-description bridge via /chat/completions instead, mirroring gemini-generator's phrasing-intensity vocabulary (strict/moderate/loose) for cluster consistency. Structurally follows gemini-generator (this registry's real, fully-built BYOK sibling) as the intended template: one skill_id, one router SKILL.md, scripts/ folder, shared media-anchor-profile schema for --anchor-profile. A real architectural question was raised and resolved before this build started: whether a Scriptorium skill holding/using an Elixverse API key contradicts CLAUDE.md principle 8 ('Scriptorium never integrates an AI backend') and the 2026-07-26 DECISIONS_PENDING.md resolution on the same topic. thatlq1812 clarified directly: it does not conflict -- this skill's scripts never embed or manage the key themselves (BYOK, same as gemini-generator/gpt-generator/claude-generator's own documented reasoning: the calling agent supplies its own credential); the actual key-holding/operational context is a separate future consuming product ('scriptorium workspace'), not this repo's core. The root .env used during this build is a local test credential for verifying the skill works, not a design element of the skill itself."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["image"]
---

# elixverse-generator

> [!WARNING]
> **PAUSED (thatlq1812 decision, 2026-08-19) — not recommended for production use.** `skill-exporter` refuses to export this skill (`registry/skills.json`'s `operational_status.state == "paused"`). Reason: Elixverse's own infrastructure does not yet support native reference-image input for image generation -- confirmed by reading the real platform source (`D:/elix/platform/server/src/api/v1/images.py`'s `ImageGenerationRequest` has no image field; `gemini_adapter.py.generate_image()` calls `generate_content(contents=[prompt])` with no image parts even though the underlying model supports it; `openai_adapter.py.generate_image()` calls `images.generate`, not `images.edit`). This is a gap in Elixverse's own adapter wiring, not a model-capability gap on Gemini/OpenAI's side -- filed as a real backlog item in `D:/elix/platform/docs/TODO.md` ("Images API — no reference-image / image-to-image support"). The code below is left in place and fully working -- built, security-audited, verified real end-to-end (see "Verified") -- because the current text-description-bridge anchor (see "Anchor design") is a real, usable substitute today; paused rather than deleted so a future session can resume once the platform gap closes and re-verify whether native conditioning (like `gemini-generator`'s) becomes possible.

An image-generation toolkit via Elixverse's OpenAI-compatible REST API (BYOK, the user's own `ELIXVERSE_API_KEY`). Image only for now -- Elixverse's docs also list `/videos/generations` and `/audio/speech`, but this skill's first build is scoped to what PROJECT.md asked for (image); those are real future extensions, not built here.

## Important — doesn't contradict the "no AI backend integration" principle

`docs/specs/STRATEGY_SPEC.md` §2 / `CLAUDE.md` principle 8 says Scriptorium doesn't integrate any AI backend -- that principle is about **Scriptorium itself** never sitting in the middle as a service calling an AI API on someone's behalf using Scriptorium's own credentials. This skill is different in nature, same as `gemini-generator`: it's an instruction for the calling agent to hit Elixverse's REST API **using the credentials of the user actually running the skill** (bring-your-own-key), entirely optional. Scriptorium never issues the key, manages billing, or requires its use -- these scripts read `ELIXVERSE_API_KEY` from the environment (or `--api-key`) exactly like `gemini-generator` reads `GEMINI_API_KEY`. Confirmed directly by thatlq1812 (see `metadata.elicited_from`): the actual key-holding operational context is a separate future product ("scriptorium workspace"), not this repo.

## Anchor design — why identity/style anchoring works differently here than in gemini-generator

`gemini-generator`'s image generation passes reference images directly into the model call (native multimodal conditioning). Elixverse's `/images/generations` **cannot do this** -- verified against the real server-side request schema (`D:/elix/platform/server/src/api/v1/images.py`, `ImageGenerationRequest`): it only accepts `prompt`/`model`/`size`/`quality`/`n`/`style`/`response_format`, no image field at all.

So this skill's anchor mechanism is a two-stage bridge instead:
1. A reference image is described in words via a vision-capable `/chat/completions` call (`image_url` content-part, per Elixverse's documented Vision support) -- either an IDENTITY description (face/character features) or a STYLE description (palette/lighting/rendering technique).
2. That text description is folded into the final `/images/generations` prompt as a strength-graded instruction (`strict`/`moderate`/`loose` phrasing intensity -- same vocabulary as `gemini-generator`, since neither API exposes a numeric conditioning scale through a prompt-only interface).

A pure-text anchor (`--identity-description`/`--style-description`, no image) skips stage 1 entirely.

## `generate_image.py`

```bash
export ELIXVERSE_API_KEY="elix_sk_..."   # or --api-key
python skills/media/elixverse-generator/scripts/generate_image.py "a watercolor fox in a forest" output.png
```

**Style-anchoring** — `--style-ref output.png --style-strength strict` describes the reference image's style via `/chat/completions`, then folds it into the prompt. Repeat `--style-ref` to stack multiple images into one synthesized style description.

**Identity-anchoring** — `--identity-ref character_face.png --identity-strength moderate` is an INDEPENDENT channel from style, same split as `gemini-generator`: preserves described face/character features while leaving pose/camera/background free to change. Combine both for "same character, new pose, new style."

**Text-only anchors** — `--identity-description "..."` / `--style-description "..."` skip the vision-description step entirely (no reference image needed, or supplement one).

**Anchor by shared profile file** — `--anchor-profile hero.json` reads a `media-anchor-profile` JSON file (see `skills/media/media-anchor-profile/SKILL.md`) instead of re-typing raw flags; mutually exclusive with the raw `--identity-*`/`--style-*` flags. Each declared block's `reference_images` are described via `/chat/completions` and combined with the block's own `description` field if both are present.

**Model selection** — `--model` (image-gen model, default: admin/auto per Elixverse convention) and `--vision-model` (model used only for the internal reference-description step, default: admin/auto) are independent flags -- the vision step and the final image-gen call can be routed to different underlying models.

**Real request fields** — `--size` (default `1024x1024`), `--quality` (default `standard`), `--n` (default `1`, multiple outputs get `_0`/`_1`/... suffixed onto `output_path`), `--render-style` (Elixverse's own `style` field, e.g. `vivid`/`natural` -- NOT the same thing as `--style-ref`/`--style-description` above, deliberately named differently to avoid confusion), `--response-format` (`url`/`b64_json`, default `b64_json`).

**A real finding: response image bytes don't always match the output extension.** Elixverse's "auto" provider routing picks the backend model server-side -- a request written to `output.png` can come back as real JPEG bytes depending on which provider was routed to (observed for real, 2026-08-19: same call, `.png` filename, actual bytes were JPEG). `generate_image.py` detects this via magic bytes and prints a `WARNING` to stderr rather than silently writing mismatched bytes -- pin `--model` if a consistent format is required.

**Credit transparency** — every response's `usage.credit_cost` is printed after generation; Elixverse's own docs are explicit that pricing is dynamic per-model, never a fixed rate, so this skill never assumes or displays an estimated cost before calling.

## `analyze_reference.py`

Standalone vision-analysis, same logic `generate_image.py` calls internally for `--identity-ref`/`--style-ref` -- useful for inspecting a description directly or preparing text for a `media-anchor-profile`'s `description` field:

```bash
python skills/media/elixverse-generator/scripts/analyze_reference.py reference.png --kind style
python skills/media/elixverse-generator/scripts/analyze_reference.py face1.png face2.png --kind identity
```

## What this skill does NOT do

- Does not supply/manage the API key -- BYOK only, same as `gemini-generator`.
- Does not generate video or audio -- Elixverse's docs list `/videos/generations` and `/audio/speech`, but PROJECT.md scoped this build to image only; a future round can extend this skill the same way `gemini-generator` covers all 3 modalities in one skill_id, rather than spinning up a separate skill.
- Does not achieve true native image-conditioning -- the identity/style anchor is a text-description bridge (see "Anchor design" above), not pixel-level conditioning; results depend on how well the vision-description step captures what matters, same class of limitation `gemini-generator`'s prompt-only style-strength phrasing already documents.
- Does not batch-generate from a manifest (unlike `gemini-generator`'s `--batch`) -- not asked for in this build's scope; a real future addition if needed, not built speculatively here.
- Does not assert Elixverse's `/images/generations` output format is fixed -- see the JPEG-vs-`.png` finding above.
- Does not upload to cloud storage, write to a database, or retry failed requests automatically.

## Bundled files

```
skills/media/elixverse-generator/
└── scripts/
    ├── elixverse_client.py   # shared HTTP client (auth, /chat/completions vision, /images/generations) -- not a CLI itself
    ├── generate_image.py     # main CLI: single-image generation + full anchor support
    └── analyze_reference.py  # standalone CLI: vision-based reference-image description
```

## Verified

Real API calls against `https://api.elixverse.com/api/v1` with thatlq1812's own Elixverse API key (2026-08-19):
- Basic single-image generation: real call, real ~450KB image written, `credit_cost` printed correctly (1190/1167 credits across 2 runs).
- `analyze_reference.py --kind style`: real `/chat/completions` vision call against the generated apple-photo image, returned a real, specific style description (palette/lighting/composition).
- `generate_image.py --style-ref ... --style-strength strict`: full anchor chain -- vision-description of the reference image, folded into the final prompt, real image generated and written (563KB, verified real JPEG magic bytes).
- `generate_image.py --anchor-profile ...`: full chain through `media-anchor-profile`'s real `validate_profile.py` (passed) and `load_profile.py` (resolved reference image to bytes), fed into the same describe-then-generate path -- real image generated and written.
- Deliberately-broken cases: missing `ELIXVERSE_API_KEY` (clean `sys.exit` message, not a traceback, exit code 1); invalid API key against a real endpoint (`401 Invalid authentication token`, surfaced via `RuntimeError`, exit code 1 -- same "let it traceback, don't swallow" convention `gemini-generator`'s own `generate()` uses for its 0-image-parts case).
- Real finding during testing: response image bytes don't reliably match the requested/implied output format (`.png` filename, real JPEG bytes returned) -- `generate_image.py` was fixed to detect and warn on this via magic-byte checking (see "A real finding" above) rather than left silently wrong.

**Not independently re-tested this round**: `--identity-description`/`--style-description` (text-only anchor, no image) -- code path is simple (skips the vision-description call entirely when no reference image is given) and follows the same logic already exercised by the image-ref path, but not separately fired against the real API. `--n > 1` multi-image output naming. `--response-format url` (the download-from-URL branch of `_write_image`) -- only `b64_json` (the default) was exercised for real. `--model`/`--vision-model` pinned to a specific non-"auto" model id.

## Known limitations

**PAUSED (2026-08-19) — see the warning banner at the top of this file.** Root cause: Elixverse's own `/images/generations` + both its adapters have no reference-image input at all (verified against real platform source, `D:/elix/platform/server/src/api/v1/images.py` + `gemini_adapter.py`/`openai_adapter.py`) — a platform-side gap, filed in `D:/elix/platform/docs/TODO.md`, not a defect in this skill. Resume once that gap closes.

Same phrasing-only anchor-strength limitation as `gemini-generator` (no numeric conditioning scale) -- compounded here by the extra text-description bridge step, so anchor fidelity depends on how well `/chat/completions`' vision description captures the reference image, one more link in the chain than `gemini-generator`'s direct pixel conditioning. Image-only; video/audio not built (Elixverse's own docs cover both, real future scope). No batch mode. `--response-format url` and `--n > 1` paths are code-reviewed but not independently re-verified against the real API (see "Verified" above). Hasn't passed stage 4 (quality eval) -- not yet scheduled per registry-wide policy, see `registry/SCHEMA.md`.

## Skills this skill depends on

- `media-anchor-profile` (consumed via `--anchor-profile`, same schema `gemini-generator` uses -- verified real end-to-end above).
