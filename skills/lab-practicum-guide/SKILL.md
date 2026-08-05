---
name: lab-practicum-guide
description: Validates a lab-session practicum guide record — a required non-empty safety-notes section, a declared equipment list, and a sequential step-by-step procedure where every step has a clear instruction and a non-empty expected-outcome checkpoint — catching a step that references undeclared equipment (a typo or an omission), a gap/duplicate in step numbering, and (as a non-blocking warning) equipment declared but never used by any step; then renders a clean Markdown guide. Use when drafting or checking a lab session guide before it's handed to students. Do NOT use this to judge whether the safety notes are actually sufficient for the specific hazards involved, whether the science/procedure itself is correct, or whether the expected outcomes are calibrated right — it validates structure and cross-reference consistency only, content is always caller-supplied.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in the standard academic lab-manual structure documented broadly in public lab-safety and lab-instruction conventions: the requirement that a lab session states its hazards/safety notes before procedure steps follows the ACS 'Guidelines for Chemical Laboratory Safety in Academic Institutions' and the standard university lab-safety-plan template pattern (a stated safety section is mandatory, procedure follows). The 'procedure step + expected-outcome checkpoint' shape (each step names what equipment/materials it uses and what a student should observe/verify to know the step worked) is the same practical structure used across public university lab-manual templates and TA-training guides for running a lab section -- a widely-taught, publicly documented convention, not a niche tacit process, matching this project's general-capability elicitation tier (CLAUDE.md principle 4). The equipment-cross-reference check (every step's equipment_used must match a declared top-level equipment item) reuses the same 'flag an undeclared/typo'd key' discipline already proven in this repo's skills/legal-form-filler/scripts/fill_form.py. The structural-validator + Markdown-render shape (assets template, --render/--force, exit 0/1/2 codes) follows skills/competency-rubric-builder/scripts/validate_rubric.py and skills/legal-research-brief/scripts/validate_legal_brief.py."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["lab-guide"]
---

# lab-practicum-guide

Validates a lab-session practicum guide record for structural soundness — safety notes present, equipment declared and cross-referenced consistently against the steps that use it, every step carrying a clear instruction and expected-outcome checkpoint — then renders it to clean Markdown. Content itself (the actual safety wording, procedure text, science) is always caller-supplied; this is a structural validator, not a content author or a safety authority.

## Why this skill, and why this scope

A TA or graduate student running a lab section needs the session guide to be internally consistent before handing it to students: a safety section that's actually present, an equipment list that actually matches what the steps reference, and a procedure where every step tells the student what "done correctly" looks like. These are all mechanically checkable properties, not judgment calls — the standard academic lab-manual shape (safety notes, equipment/materials list, numbered procedure with checkpoints) is public, widely-taught convention (ACS lab-safety guidelines, standard university lab-manual/lab-safety-plan templates), so this skill is general-capability tier per CLAUDE.md principle 4: no expert interview needed, public-source grounding is sufficient.

## What a structurally sound lab guide requires (the domain knowledge this validator encodes)

- **A non-empty `safety_notes` list**, each entry a non-empty string. A lab guide with no stated safety notes is refused outright — this only checks the section is present and non-empty, never that it's actually sufficient for the real hazards involved.
- **A non-empty `equipment` list** with no duplicate entries.
- **A non-empty `steps` list**, each step with a unique, sequential `step_number` (starting at 1, no gaps), a non-empty `instruction`, and a non-empty `expected_outcome` — the checkpoint a student/TA uses to verify the step actually worked before moving on.
- **Equipment cross-reference**: every item in a step's `equipment_used` must appear in the top-level `equipment` list — a hard error, catching a typo'd or omitted equipment declaration. An equipment item declared but never referenced by any step is a non-blocking warning (it may legitimately be optional/backup equipment).

## Run

```bash
python scripts/validate_lab_guide.py <guide.json> [--render guide.md] [--force]
```

Start from `assets/lab_guide_template.json` (a valid 3-step Ohm's Law verification lab — read it for the exact JSON shape: `title`, optional `course`, `safety_notes[]`, `equipment[]`, `steps[].{step_number, instruction, equipment_used, expected_outcome}`). Exit 0 = structurally valid (warnings may still print — unused-equipment flags), exit 1 = errors block (printed with exact step/field detail), exit 2 = malformed input, or `--render` target already exists without `--force`. `--render` only writes output when there are zero errors.

## What this skill does NOT do

- Doesn't judge whether the stated safety notes are actually sufficient for the real hazards of the lab, whether the procedure's science is correct, or whether an expected outcome is calibrated to a reasonable tolerance — pure structural/cross-reference validation, content is always the caller's responsibility.
- Doesn't generate guide content itself (no LLM/AI call) — the TA/instructor (or the agent working with them) writes the JSON; this only checks it.
- Doesn't produce a formatted `.docx`/`.pdf` handout — delegate that to `office-doc-creator` once the Markdown passes validation.
- Doesn't check equipment/safety terminology against any specific institutional EHS (Environmental Health & Safety) policy or chemical-specific SDS (Safety Data Sheet) requirements — that is real institution-specific compliance knowledge out of scope for this general-capability skill.

## Verified

The bundled 3-step Ohm's Law lab guide (3 safety notes, 5 equipment items, all referenced) validated with zero errors/warnings and rendered correctly to Markdown with Safety Notes / Equipment / Procedure sections. Deliberately broken cases: an empty `safety_notes` list correctly refused; a step referencing an undeclared equipment item (`oscilloscope`, never in the equipment list) correctly refused by exact name, combined in the same run with a step carrying an empty `expected_outcome` (also correctly refused, both errors shown); a step-numbering gap (`[1, 3]` instead of `[1, 2]`) correctly refused showing the actual vs. expected sequence; a guide with equipment declared but never used by any step (`backup power supply`) correctly passed with exit 0 and a non-blocking warning naming the unused item; malformed (non-JSON) input correctly refused with exit 2.

## Known limitations (v0.1.0)

- The equipment cross-reference check is exact-string matching — a step referencing "multimeter" when the equipment list declares "digital multimeter" is flagged as undeclared even though a human would recognize them as the same item, the same deliberate no-fuzzy-matching tradeoff `legal-form-filler`'s `check_dossier.py` makes.
- No check that `expected_outcome` text is actually falsifiable/measurable (e.g. "should work" vs. "reading within 10% of 220 ohm") — presence/non-emptiness only, not quality of the checkpoint's wording.
- No institution-specific safety-compliance checking (chemical hazard classes, SDS references, EHS sign-off requirements) — out of scope, see "What this skill does NOT do."
- `--render`'s Markdown always lists steps sorted by `step_number`, regardless of the order they appear in the input JSON — this is deliberate (rendered output should always read in procedure order) but means the render does not preserve the JSON's original array order if it was already out of numeric order (which would itself have failed validation anyway, since step_number must be sequential).
