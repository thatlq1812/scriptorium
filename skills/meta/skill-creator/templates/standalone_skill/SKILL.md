<!--
================================================================================
  GOLD TEMPLATE — Scriptorium STANDALONE skill

  A standalone skill is invoked directly by a user or agent to produce a
  deliverable (a converted file, a generated asset, a draft document). This
  is the template for skills like document-ai-structurer, office-doc-creator,
  image-generator-gemini.

  This is a REFERENCE SKELETON. skill-creator copies this folder to
  skills/<name>/, fills the <...> slots, then deletes every <!-- --> block
  (including this one) — a real skill ships with NO comment blocks.

  COMMENT LEGEND:
    ★ REQUIRED — must be filled, cannot be dropped.
    ◆ CHOOSE   — skill-specific, pick per the inline guidance.

  Before filling this in, confirm skill-creator's precondition is met:
  elicited tacit process (from a real source) + grounded research both
  exist. If not, stop — see skills/meta/skill-creator/SKILL.md.
================================================================================
-->
---
# ★ name: lowercase letters/numbers/hyphens only, MUST equal the parent folder
#   name under skills/. <=64 chars.
name: <skill_id>
# ★ description: <=1024 chars. State BOTH what the skill does AND when to
#   use it / when not to. This is the primary triggering signal — the
#   consuming agent decides whether to use the skill from this text alone.
#   Write it slightly "pushy" (spell out phrasings a user might actually
#   type), not a neutral one-liner. See skill-creator/SKILL.md for the
#   trigger-eval self-check (8-10 should-trigger + 8-10 should-not-trigger
#   questions) before finalizing this field.
description: <what it does>. Use when <concrete trigger conditions>. Do NOT use when <concrete exclusion>.
# ★ license: SPDX identifier. If any part is adapted/harvested from an
#   outside source, it must match that source's real license and have
#   passed license-compliance-check — never default to MIT without checking.
license: MIT
# ★ compatibility: <=500 chars. List ONLY harnesses actually verified
#   running, with a date. Leave empty/omit until at least one real
#   verification has happened — never infer from a vendor showcase.
compatibility: <dependencies + verified harnesses, or "not yet verified on any harness">
metadata:
  # ★ domain: reference SkillsMP occupation groups; use `general` if the
  #   skill is equally useful across every domain, `meta` if it operates
  #   Scriptorium itself (rare for a standalone skill — that's usually a
  #   dependency skill instead, see templates/dependency_skill/).
  domain: <general | specific-domain>
  # ★ task_type: research | document-conversion | drafting | review-qa | coordination
  task_type: <task_type>
  # ★ risk_tier: N1 (low, e.g. lookup/format conversion) .. N5 (high, e.g.
  #   contract drafting — mandatory human gate). See registry/SCHEMA.md.
  risk_tier: <N1-N5>
  # ★ source: self-authored, or harvested (then source.repo_url/commit go in
  #   the registry entry, not here).
  source: self-authored
  # ★ elicited_from: the REAL source of tacit knowledge/research behind this
  #   skill. Never empty, never invented — this is what separates a curated
  #   skill from a self-generated one (SkillsBench: self-generated = no
  #   benefit on average).
  elicited_from: "<real elicited source: an owner project reviewed, a paper, a research session, an expert consulted>"
  # ◆ engine/dependencies-related metadata as needed (e.g. `engine: "docling==2.115.0"`)
  version: 0.1.0
---

# <skill_id>

<!-- ★ One paragraph: what this skill converts/produces, and why this exact
     design was chosen — tie back to elicited_from, not invented reasoning. -->

## When to use

<!-- ★ Concrete conditions this skill applies to. Mirror description but with
     more room — this is where an agent double-checks after description
     already triggered it. -->

## <Bootstrap / setup section — ◆ only if the skill needs Python or another runtime>

<!-- ◆ If Python is needed: use the SHARED venv via toolchain-bootstrap, never
     a per-skill venv. See skills/general/toolchain-bootstrap/SKILL.md for the exact
     invocation. Delete this section entirely if the skill is pure
     instructional (no script). -->

## Process

<!-- ★ Concrete, numbered steps another agent can follow without asking
     clarifying questions. Not narrative prose. -->

## What this skill does NOT do

<!-- ★ Explicit exclusions — especially anything a reader might assume this
     skill handles but doesn't (adjacent skills, out-of-scope formats, etc.). -->

## Bundled files

<!-- ◆ List every file under scripts/ / references/ / assets/ with a one-line
     purpose each. Delete this section if the skill is pure SKILL.md. -->

## Known limitations (v0.1.0)

<!-- ★ Real gaps, not hedging. What hasn't been tested, what a future version
     should add. Every skill ships with this section honest and populated —
     "no known limitations" is a red flag, not a compliment. -->
