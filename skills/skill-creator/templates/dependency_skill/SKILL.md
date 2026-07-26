<!--
================================================================================
  GOLD TEMPLATE — Scriptorium DEPENDENCY skill

  A dependency skill is not invoked directly for a deliverable — it's
  infrastructure other skills lean on (python-env-bootstrap,
  license-compliance-check, dedup-novelty-check). It's leaner than a
  standalone skill: no "produces a deliverable" framing, usually a
  short, procedural, or check/verdict shape.

  This is a REFERENCE SKELETON. skill-creator copies this folder to
  skills/<name>/, fills the <...> slots, then deletes every <!-- --> block.

  COMMENT LEGEND:
    ★ REQUIRED — must be filled, cannot be dropped.
    ◆ CHOOSE   — skill-specific, pick per the inline guidance.
================================================================================
-->
---
name: <skill_id>
# ★ description: state what this skill does for a CALLER (another skill or
#   agent), when to invoke it, and explicitly that it's infrastructure, not
#   a direct user-facing deliverable producer (unless it genuinely is both).
description: <what it does>. Use when <another skill/step needs this capability>. Do NOT use for <adjacent thing that's a different skill's job>.
license: MIT
compatibility: <verified harnesses + any external tool dependency (e.g. requires `uv`, requires `gh` CLI)>
metadata:
  # ★ domain: almost always `meta` for a dependency skill (it operates
  #   Scriptorium's own pipeline), unless it's a general-purpose utility
  #   other domain skills call (then `general`).
  domain: meta
  # ★ task_type: coordination is the most common fit for dependency skills;
  #   review-qa if it's a check/verdict skill (like license-compliance-check).
  task_type: <coordination | review-qa | research>
  risk_tier: <N1-N5>
  source: self-authored
  elicited_from: "<real elicited source>"
  # ◆ pipeline_stage: <1-9> — set if this skill IS one of the 9 bootstrap
  #   pipeline stages (docs/specs/STRATEGY_SPEC.md §3). Omit otherwise.
  version: 0.1.0
---

# <skill_id>

<!-- ★ One paragraph: what problem this solves FOR ANOTHER SKILL, and why it
     needed to exist as a shared dependency instead of being duplicated
     inline in every skill that needs it. -->

## Process

<!-- ★ Concrete steps. If this is a check/verdict skill, state the exact
     decision rule (like license-compliance-check's SAFE/BLOCKED
     classification) rather than vague "evaluate carefully" language. -->

## What this skill does NOT do

<!-- ★ Explicit boundary with adjacent pipeline stages — dependency skills
     are especially prone to scope creep into a neighboring stage's job. -->

## Skills depending on this skill

<!-- ◆ List skill_ids that declare this in their registry `dependencies` —
     keep updated as more skills adopt it. -->

## Known limitations (v0.1.0)

<!-- ★ Real gaps. -->
