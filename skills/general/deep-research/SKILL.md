---
name: deep-research
description: A protocol for conducting rigorous multi-source research on an open question and packaging the result as a grounded, machine-checkable brief — not a research API. The calling agent does the actual searching/reading using whatever tools it already has (web search, file access, a database); this skill supplies the decomposition/grounding discipline and a validator that catches a fabricated or mistyped citation before the brief is trusted. Use when a question needs multiple sources triangulated and an honest account of gaps/contradictions/confidence, not a single quick lookup. Do NOT use this skill expecting it to search or call an AI itself — it has no network access and calls no AI backend; it is instructions + a validator, executed by whichever agent's own model is already running.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (json, argparse, re) — no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-07-27). See "Known limitations" section below for real test-case detail.'
metadata:
  domain: general
  task_type: research
  risk_tier: N2
  source: self-authored
  elicited_from: "thatlq1812 (2026-07-27): explicit request for a deep-research capability, clarified during discussion in important.md that it must NOT mean Scriptorium holding its own AI provider key ('base AI backend but with other way') — the intended shape is a skill that gives any calling agent the same rigor an agent doing research live already applies (decompose, triangulate, cite, flag gaps), packaged so it can be run by an agent that doesn't already have this discipline built in. Schema and validator pattern directly reused from this repo's own legal-research-brief (elicited from outside_research/research_01_result_01.md's legal-opinion output schema, itself grounded in Stanford RegLab/HAI's 'Hallucination-Free?' findings on legal-AI citation fabrication, docs/specs/STRATEGY_SPEC.md §5.2), generalized here beyond the legal domain to any research question."
  version: 0.1.0
  grounding: required
  object_type: []
---

# deep-research

A protocol, not a research API. This skill never searches the web, calls an AI provider, or holds any API key — Scriptorium does not integrate an AI backend (`docs/specs/STRATEGY_SPEC.md` §2, non-negotiable). What it provides instead: a decomposition/grounding discipline for the calling agent to follow while doing the research itself with tools it already has, plus a deterministic validator that catches a fabricated or mistyped citation before the resulting brief is trusted — the same discipline `citation-management` and `legal-research-brief` already apply, generalized past the legal domain.

## When to use

Use when a question genuinely needs multiple sources triangulated, contradictions surfaced, and an honest confidence/gaps statement — not a single quick lookup a normal tool call already answers. Especially useful when the calling agent/harness doesn't already have a rigorous research habit built in (thatlq1812's own observation: not every agent does this well by default even when it technically has web access).

Don't use when: one authoritative source already answers the question (just cite it directly, no need for the full brief structure); or the goal is legal research specifically (use `legal-research-brief` instead — same discipline, Vietnamese-legal-opinion-shaped schema, and a hiệu lực-status caveat this general skill doesn't carry).

## Protocol (followed by the calling agent, not by any script here)

1. **Decompose** the question into concrete sub-questions — don't research an open-ended topic as one blob.
2. **Search and read**, using whatever tools you already have (web search, `document-ai-structurer`-structured local corpora, a database) — this skill supplies none of that itself.
3. **Record every source** as you use it: id, title, url (or `local:<path>` for a non-web source), and the date you accessed/read it — not retroactively from memory afterward.
4. **Write findings as individually cited claims** — a claim with no source is not a finding, it's a guess.
5. **State gaps and contradictions explicitly**, even if the honest answer is "none identified" — never omit the field to imply nothing was found when you didn't actually check.
6. **Give a confidence level and say why** — "high confidence, 3 independent sources agree" is different from "medium confidence, only 1 source found."
7. **Write the synthesis with inline `[S1]`-style citation markers on every claim it makes** — a synthesis paragraph with zero citation markers fails validation outright; it's treated as unsourced narrative.
8. **Validate before trusting the brief**:
   ```bash
   python skills/general/deep-research/scripts/validate_research_brief.py brief.json --render brief.md
   ```
   Exit 0 = every finding and every inline synthesis citation traces to a real, declared source. Exit 1 = errors (each naming the exact field/index and reason — including a citation marker used inline in `synthesis` that doesn't exist in `sources`, not just citations inside `findings`). Exit 2 = malformed input.

Start from `assets/research_brief_template.json` for the exact schema.

## What this skill does NOT do

- Does not search anything itself — zero network access in `validate_research_brief.py`.
- Does not call any AI/LLM API — Scriptorium never does (`docs/specs/STRATEGY_SPEC.md` §2/§6/§7.4).
- Does not verify a cited source's *content* actually supports the claim — only that the citation points to a *declared* source, exactly like `legal-research-brief`'s equivalent limitation. A human/agent must still confirm the characterization is accurate.
- Does not generate the brief for you — there is no scaffold generator here (deliberately, after this project's own v0.2.0 hardening round found an ungated generator was the exact failure mode in `hypothesis-generation` and `peer-review`); the agent writes the brief from real research, this skill only validates it.

## Verified

The bundled template passes clean and renders correctly; a deliberately broken brief (fabricated finding-level citation, an empty-cites finding, an invalid confidence value, a missing confidence_rationale, a synthesis with zero citation markers) caught all 5 errors; a fabricated citation marker inline in synthesis text (not in any finding) caught separately; malformed JSON and render-overwrite-without-force both correctly refused.

## Known limitations (v0.1.0, not yet through official quality-eval)

- Citation checking is by source id only, not by content — a claim citing a real, declared source that actually misrepresents what that source says will still pass.
- No check that `sub_questions` were actually all addressed by `findings` — decomposition quality is not mechanically verified, only that whatever findings exist are grounded.
- Verified only against hand-authored fixtures this session, not yet exercised as part of a real end-to-end research task by an agent.
- Hasn't passed stage 4 (quality eval, ≥2 harnesses) or stage 5 (security audit — self-audited only this session: stdlib-only, no eval/exec/subprocess/os.system/network calls found).
