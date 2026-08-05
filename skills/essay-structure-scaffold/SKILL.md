---
name: essay-structure-scaffold
description: Validates/scaffolds an academic essay's structural outline — checks a thesis statement is present, every body paragraph has a topic sentence, non-empty supporting evidence, and an explicit link back to the thesis, and the conclusion restates the thesis rather than silently going missing; a lexical (not semantic) heuristic also flags when a paragraph's link-back shares no words with the thesis or when the conclusion contains words absent from the rest of the outline, a possible sign of a new claim. Renders a validated outline to clean Markdown. Use when drafting or reviewing an essay's argumentative skeleton before or instead of full prose. Do NOT use this to write, grade, or judge the quality/persuasiveness of essay content — the writer (or the calling agent working with the writer) always supplies the actual thesis/topic-sentence/evidence/conclusion text; this only checks the outline's structure and does simple word-overlap heuristics.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, re, argparse) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-29). See "Verified" section below for real test-case detail.'
metadata:
  domain: education
  task_type: review-qa
  risk_tier: N1
  source: self-authored
  elicited_from: "Grounded in the standard five-paragraph/thesis-body-conclusion academic essay structure documented across widely-taught public sources on academic writing (e.g. Purdue OWL's argumentative-essay guidance, the standard 'topic sentence + evidence + link back to thesis' body-paragraph shape, and the 'conclusion restates without introducing new claims' rule taught in most university writing-center handouts) — general-capability tier per CLAUDE.md principle 4, public-source grounding, no expert interview needed. Scoped as a pure structural validator, never a content generator, matching the same 'checklist/template caller-supplied, script validates structure/arithmetic only' posture already established by competency-rubric-builder and assessment-builder in this repo (structure and lexical pattern-matching decide pass/fail, never a judgment call about content quality)."
  version: 0.1.0
  grounding: not_applicable
  object_type: ["essay"]
---

# essay-structure-scaffold

Validates an academic essay's structural outline — thesis, body paragraphs, conclusion — then renders it to clean Markdown. Catches a missing thesis, an under-supported body paragraph, or a missing conclusion deterministically, before the essay's prose is drafted or reviewed. Also runs two lexical (word-overlap, not semantic) heuristics: whether a paragraph's link-back actually shares vocabulary with the thesis, and whether the conclusion introduces vocabulary absent from the rest of the outline — a cheap, mechanical proxy for "may not actually restate the thesis" or "may introduce a new claim," always printed as a warning to review, never as a blocking error.

## Why this skill, and why this scope

The five-paragraph/thesis-body-conclusion essay structure — thesis statement, each body paragraph built from a topic sentence, supporting evidence, and an explicit tie back to the thesis, and a conclusion that restates rather than introduces new claims — is standard, publicly-documented academic-writing guidance (Purdue OWL and equivalent university writing-center material), not a niche or tacit practice, so this is general-capability tier per CLAUDE.md principle 4: public-source grounding is sufficient, no expert interview needed.

This skill deliberately does the same thing `competency-rubric-builder` and `assessment-builder` already do for their own artifacts: validate structure and do cheap, explainable, mechanical checks, and refuse to generate or judge content. An essay's actual argument quality, evidence strength, or prose style requires real judgment this skill does not attempt to automate — a structurally "VALID" outline says nothing about whether the essay would be a good one.

## What a structurally sound outline requires (the domain knowledge this validator encodes)

- **A thesis statement**: `thesis_statement`, a non-empty string.
- **At least one body paragraph**, each with:
  - `topic_sentence` — non-empty string.
  - `evidence` — a non-empty list of non-empty strings (each item is one piece of supporting evidence).
  - `link_back_to_thesis` — non-empty string, an explicit sentence tying the paragraph back to the thesis.
- **A conclusion**: `conclusion.restates_thesis`, a non-empty string.

Two additional lexical heuristics run on top of the structural checks (warnings, never hard errors, since both are word-overlap pattern matching, not content understanding):

- A paragraph's `link_back_to_thesis` sharing zero content words with `thesis_statement` is flagged — a real signal the link-back may be generic filler rather than an actual tie back to the thesis.
- A word appearing in `conclusion.restates_thesis` that appears nowhere else in the thesis or any body paragraph is flagged — a real signal (not proof) the conclusion may be introducing a claim that was never argued in the body.

## Run

```bash
python scripts/validate_essay_structure.py <outline.json> [--render outline.md] [--force]
```

Start from `assets/outline_template.json` (a valid, warning-free 2-paragraph example on urban community gardens and food security — read it for the exact JSON shape). Exit 0 = structurally valid (warnings may still print — read them, they flag possible weak link-backs or new claims in the conclusion), exit 1 = errors block (printed with field-level detail: exact paragraph index and missing field), exit 2 = malformed input, or `--render` target already exists without `--force`. `--render` only writes output when there are zero errors.

## What this skill does NOT do

- Doesn't write or generate any essay content (thesis, topic sentences, evidence, or conclusion) — the writer or calling agent always supplies the outline; this only checks it.
- Doesn't judge argument quality, evidence strength, source credibility, or prose style — pure structural + lexical-overlap validation. Pair with `academic-source-finder` to validate the *sources* an essay's evidence cites.
- Doesn't do semantic understanding of "new claim" or "restates" — the conclusion/link-back heuristics are word-overlap only. A conclusion that restates the thesis in entirely different vocabulary (a well-written paraphrase) will trigger a false-positive warning; a conclusion that smuggles in a new claim using only words already used elsewhere in the outline will trigger no warning at all. Both are printed as warnings to review, never as blocking errors, for exactly this reason.
- Doesn't validate citation format or source credibility for the `evidence` entries — that's `academic-source-finder` and `citation-management`'s scope, not this skill's.
- Doesn't produce a final formatted document — delegate to `office-doc-creator` once the outline (and later, the drafted prose) is ready.

## Verified

`validate_essay_structure.py`: the bundled `assets/outline_template.json` (thesis + 2 body paragraphs + conclusion, conclusion vocabulary deliberately reused from the thesis/body) validated with **zero errors and zero warnings**, and `--render` produced a correct Markdown outline. A JSON object missing `thesis_statement` entirely and with an empty `body_paragraphs` list was correctly refused, naming both missing fields (exit 1). A paragraph with an empty `evidence` list, an empty-string `link_back_to_thesis`, and an empty `conclusion` object were all correctly refused, each naming the exact field/index (exit 1). A structurally valid outline where a paragraph's `link_back_to_thesis` was unrelated filler text ("Basketball teams often practice in the evening after school") and the conclusion introduced an unrelated new claim ("the government should ban gasoline-powered vehicles by 2030") passed structurally (exit 0) but correctly triggered both lexical warnings, naming the exact unmatched words. Malformed JSON was correctly refused (exit 2, exact parse error reported).

## Known limitations (v0.1.0)

- The new-claim and link-back heuristics are lexical (word-overlap after stopword filtering), not semantic — a well-paraphrased conclusion using different vocabulary than the thesis produces a false-positive warning, and a smuggled-in new claim phrased using only words already present elsewhere produces no warning at all. Both are explicitly labeled "review manually" in the warning text for this reason.
- The bundled stopword list is a small, manually-reviewed general-English list, not a real NLP stopword corpus or lemmatizer — plural/verb-form variants of the same word (e.g. "improve" vs "improving") are treated as different tokens and can trigger a spurious warning even when the underlying concept is identical.
- No check on paragraph count, ordering, or essay length — a one-paragraph or twenty-paragraph outline is equally valid as long as each paragraph is structurally complete; genre/length requirements (e.g. "exactly five paragraphs") are out of scope, left to the writer's assignment instructions.
- Does not validate that `evidence` entries are real, citable, or accurately represent a source — that grounding responsibility belongs to `academic-source-finder`, not this skill.
