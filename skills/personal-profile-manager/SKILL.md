---
name: personal-profile-manager
description: Local-only personal profile store and behavior-adaptation proposal generator for non-tech users. `init_profile.py` scaffolds a local `personal/profile.json` (identity, organization, tax ID, contact) from a bundled template; `validate_profile.py` checks it has the required sections/fields before trusting it; `autofill.py` resolves a caller-declared field_map (target form field mapped to a profile dotted-path) against the profile, refusing to invent values for anything unresolved; `propose_style_update.py` turns a feedback log into a PROPOSED CLAUDE.md/AGENTS.md instruction-update block, never auto-applied. Use when a user wants to stop re-typing the same identity/org details into every form, contract, or lesson plan, or wants the agent's tone/register to adapt to explicit feedback. Do NOT use this to auto-apply a style change to system instructions without human review, and do NOT use it as a place to store secrets/credentials -- it is a plain local JSON file, not a secret store.
license: MIT
compatibility: Requires Python 3.11+, stdlib only (json, argparse, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29).
metadata:
  domain: general
  task_type: coordination
  risk_tier: N2
  source: self-authored
  elicited_from: "Owner direction 2026-07-29 (docs/ROADMAP.md 'New planned roadmap items', UPGRADE_PLAN_20260729.md Item 1), grounded in the owner's real non-tech-user pilot need (repeating identity/org details across forms, dossiers, contracts, lesson plans) rather than an invented feature. Field schema (identity/organization/contact) cross-checked against what legal-form-filler/office-doc-creator/lesson-plan-builder's own input schemas actually ask for, not designed from scratch. Local-config-file convention (single JSON, separate from credentials) lightly grounded against AWS CLI's config/credentials split and cookiecutter's variables-file pattern (public convention survey, not a cloned dependency -- deliberately kept stdlib-only rather than adopting a templating engine)."
  version: 0.1.1
  changelog_0_1_1: "Doc-only: documented and verified real chaining into legal-form-filler's fill_form.py -- autofill.py's output already matches that skill's form_data.json shape with zero conversion needed (docs/DECISIONS_PENDING.md resolved item 9). No script change."
  grounding: not_applicable
  object_type: ["profile", "form"]
---

# personal-profile-manager

Two independent halves: a local personal-data profile store with a generic auto-fill engine, and a writing-style feedback-to-proposal pipeline. Both are local-only, no network calls, no AI backend.

## Why this skill, and why this scope

A recurring real cost for non-tech users (teachers, lawyers, other professionals) working with Scriptorium-produced skills is re-typing the same identity/organization/contact details into every form, dossier, contract, or lesson plan a downstream skill asks for. Rather than have each downstream skill invent its own profile-storage convention, this is one shared local store plus a generic field-mapping engine -- same "generic engine, caller supplies the specifics" shape as `legal-form-filler` (which never hardcodes a checklist/template, only validates against one the caller supplies).

The behavior-adaptation half is a separate, smaller capability bundled here because it's the same underlying idea (adapting to *this user specifically*) but is NOT the same mechanism -- it never writes to system instructions directly. A script proposing a change to CLAUDE.md/AGENTS.md and applying it silently would be the same ungated-generator failure mode the v0.2.0 hardening round found and fixed in `hypothesis-generation`/`peer-review` (STATUS.md's hardening-round notes) -- so this only ever proposes, printed for a human/agent to review and insert manually.

## Run

### Profile store

```bash
python scripts/init_profile.py personal/profile.json
python scripts/validate_profile.py personal/profile.json
```

`init_profile.py` scaffolds from `assets/profile_template.json`, refuses to overwrite an existing file without `--force`. `validate_profile.py` checks the 3 required sections (`identity`, `organization`, `contact`) each have their minimum required field non-empty -- exit 0 = valid, 1 = named violations, 2 = malformed/missing file.

Recommended location: `personal/profile.json` at the repo root -- `.gitignore` already excludes `/personal` by default (see "Privacy" below).

### Auto-fill

```bash
python scripts/autofill.py personal/profile.json field_map.json -o filled.json
```

`field_map.json` is always caller-supplied (start from `assets/field_map_template.json`) -- a flat `{ "target_field_name": "section.field" }` mapping from a downstream skill's own field names to a dotted path in `profile.json`. A path that doesn't resolve (typo, or the profile genuinely has no such field) is reported by name on stderr and left OUT of the output, never invented -- exit 0 = every mapped field resolved, 1 = at least one unresolved (still writes what did resolve if `-o` given; the caller must check the unresolved list before trusting the output), 2 = malformed input.

**Chains into `legal-form-filler` for real** (2026-07-29, `docs/DECISIONS_PENDING.md` resolved item 9): `autofill.py -o filled.json`'s output is already the exact flat `{field_name: value}` shape `legal-form-filler/scripts/fill_form.py` expects as its `form_data.json` argument -- no conversion script needed, pipe the output straight in:

```bash
python scripts/autofill.py personal/profile.json field_map.json -o filled.json
python skills/legal-form-filler/scripts/fill_form.py <form_template.json> filled.json
```

`fill_form.py` already tolerates extra keys in `filled.json` that a specific form doesn't declare (reports them as unmatched, doesn't fail) -- so one `profile.json`/`field_map.json` pair covering many possible fields can feed different forms without re-running `autofill.py` per form. Field VALUE format (e.g. date format) is not cross-checked between the two skills -- `personal-profile-manager` stores whatever format the profile was written in, `fill_form.py` only checks presence, not format; a real form needing a specific date format still needs that normalized by the caller.

### Behavior/style adaptation proposal

```bash
python scripts/propose_style_update.py feedback_log.json -o proposal.md
```

`feedback_log.json` (start from `assets/feedback_log_template.json`) is a list of `{date, category, feedback_text}` entries. Groups by category and prints (and optionally writes) a Markdown block explicitly marked as a **proposal**, never auto-applied to any file. Exit 0 = proposal generated, 1 = no valid entries, 2 = malformed input.

## What this skill does NOT do

- Does not auto-apply anything to `CLAUDE.md`/`AGENTS.md`/a harness system prompt -- `propose_style_update.py` only ever prints/writes a standalone proposal file for a human or the calling agent to review and manually insert.
- Does not do fuzzy/semantic field matching in `autofill.py` -- a `field_map` entry naming a path that doesn't exist in the profile is reported unresolved, same "never guess a match" discipline as `legal-form-filler`.
- Is not a secrets/credentials store -- `profile.json` is a plain local JSON file, appropriate for identity/org/contact metadata, not passwords/API keys/private keys.
- Does not decide WHICH downstream skill's fields map to which profile fields -- that mapping is always caller-declared via `field_map.json`, never hard-coded for a specific target skill.
- Does not sync/back up the profile anywhere -- purely local; a user wanting version history must opt in themselves (see "Privacy" below).

## Privacy

`.gitignore` at the repo root excludes `/personal` by default -- a `profile.json` under `personal/` never gets committed even in a repo the user later makes public. A `personal/README.md` (create alongside the first real profile) should explain this and note that users on a genuinely private repository can remove the ignore rule if they want their profile under version control.

## Verified

`init_profile.py`: fresh scaffold from template succeeded; re-running without `--force` against an existing file correctly refused (exit 1); `--force` correctly overwrote. `validate_profile.py`: the bundled template passed clean; a profile missing the `contact` section entirely was correctly refused, naming the missing section; a profile with `identity.full_name` present but empty-string was correctly refused, naming the exact field; malformed JSON correctly refused (exit 2). `autofill.py`: the bundled `field_map_template.json` against the bundled `profile_template.json` resolved all 8 fields correctly (verified value-by-value); a field_map with one path pointing at a nonexistent profile key ("identity.middle_name") was correctly reported unresolved while the other 7 still resolved and were written to output; a field_map path pointing at a nested object instead of a leaf value (e.g. `"identity"` alone) was correctly treated as unresolved, not silently serialized as a JSON object. `propose_style_update.py`: the bundled `feedback_log_template.json` (2 entries, 2 categories) produced a correctly-grouped Markdown proposal with the explicit non-auto-apply warning banner; an entries list missing a required field on one entry was correctly refused (exit 2, naming the entry index) rather than silently skipping just that entry; an empty `entries: []` list was correctly refused (exit 2). **`legal-form-filler` chaining (2026-07-29)**: `autofill.py`'s real output (from the bundled profile/field_map) piped directly into `legal-form-filler/scripts/fill_form.py` with zero conversion -- correctly identified the 6 extra fields the form didn't declare as unmatched (not an error) and correctly reported all required fields filled, exit 0. First real end-to-end downstream usage of this skill's output by another skill.

## Known limitations (v0.1.1)

- `validate_profile.py`'s required-field check is deliberately minimal (one anchor field per section, e.g. `identity.full_name`) -- it does not enforce every field in the template exists or is well-formed (no date-format or tax-ID-format validation). A future version could add per-field format rules if real use shows the need, following `legal-form-filler`'s own documented limitation in the same spot.
- `autofill.py` only resolves scalar (string/number/bool) leaf values -- a `field_map` path pointing at a nested object or list is treated as unresolved rather than serialized, since a downstream form field is assumed to want a single value, not a structure.
- Verified chained into `legal-form-filler` for real (2026-07-29, see "Verified" above) -- other candidate downstream skills (`lesson-plan-builder`, `project-workspace-initializer`'s `PROJECT.md`) haven't been wired/verified yet.
- No profile-migration/versioning story yet if the schema in `assets/profile_template.json` changes later -- an existing `personal/profile.json` from an older template version isn't automatically upgraded.
