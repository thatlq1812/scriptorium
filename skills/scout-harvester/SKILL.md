---
name: scout-harvester
description: Finds and preliminarily evaluates outside candidates (GitHub repos, libraries, papers, existing skills) for a specific Scriptorium skill need, before any content touches license-compliance-check (step 7). Use when starting a new skill and wanting to know "has anyone already solved this, and how" before designing from scratch. Does NOT decide harvest/use on its own — only proposes candidates with a preliminary evaluation; the legal go/no-go decision always belongs to license-compliance-check.
license: MIT
compatibility: A research process (web search + reading code/docs), no harness dependency for the process itself. `scripts/github_scout.py` requires the `gh` CLI on PATH; `scripts/pypi_license_check.py` is stdlib-only. Verified running clean: Claude Code (2026-07-26) — process run for real 3 times while building `document-ai-structurer`, `python-env-bootstrap`, and evaluating anthropics/skills; both scripts tested for real against mermaid-js/mermaid and 3 PyPI packages, output matched prior manual checks.
metadata:
  domain: meta
  task_type: research
  risk_tier: N1
  pipeline_stage: 6
  source: self-authored
  elicited_from: "Distilled from 3 real runs in the 2026-07-26 session: researching document-parsing tools before building document-ai-structurer, researching a python bootstrap tool before building python-env-bootstrap, and scouting anthropics/skills at owner's request — all three followed the same pattern that had never been written down as a process before"
  version: 0.2.0
---

# scout-harvester

Answers: **has anyone already done this well, and if so, is it worth learning from/using** — before `skill-creator` designs from scratch, and before any content is allowed to touch `license-compliance-check`.

## When to run

Right after identifying a need for a new skill (from elicitation or an owner request), BEFORE writing `SKILL.md`. Skipping this step = designing from zero, sometimes reasonable (a need too Scriptorium-specific to have an outside precedent, e.g. `license-compliance-check` — nothing external to scout), but it must be a deliberate decision, not the default.

## Process (distilled from 3 real runs)

### 1. Determine search scope

Three different kinds of sources, searched in different priority order depending on the need:
- **Packaged tools/libraries** (e.g. Docling, uv) — prioritize when a specific technical CAPABILITY is needed (parsing PDFs, managing a Python env). Search by: comparing several options at once (don't lock in the first one found), prefer self-hosted/no external API key needed.
- **An existing skill/repo with the same idea** (e.g. anthropics/skills) — prioritize when REFERENCE for how to present/structure a common type of skill is needed. Check major marketplaces first (skills.sh, the agentskills.io showcase) then GitHub topic search.
- **Papers/standards** (e.g. SkillsBench, llms.txt) — prioritize when methodology grounding is needed, when there's no "code to harvest" but there is "a way of thinking to learn from."

### 2. Preliminary evaluation of each candidate (NOT a deep audit — that's a later step)

For each candidate, quickly answer 4 questions, no deep investigation needed:
- Is it actually in real use/maintained (activity, adoption) or just an abandoned proof-of-concept?
- Does the input/output/capability actually match the need, or just "roughly similar"?
- What does the license LOOK LIKE at a glance (MIT/Apache/proprietary/unclear) — just note it, do NOT conclude go/no-go at this step, that's license-compliance-check's job.
- Is there a candidate clearly better than the rest (self-hosted, permissive, output matching the need) so the full comparison can stop early?

Use the bundled scripts instead of hand-typing `gh api`/`gh search`/PyPI lookups each time (the pattern this whole process was distilled from):

```bash
python scripts/github_scout.py repo <owner/repo>            # stars, license, description, topics
python scripts/github_scout.py search "<query>" --limit 10  # ranked by stars
python scripts/pypi_license_check.py <package1> <package2>  # PyPI-declared license, batched
```

Both print a rough license signal for step 2 — NOT a substitute for license-compliance-check reading the real LICENSE file at the correct level (a PyPI classifier or a GitHub API `license` field can be stale or wrong; both scripts print a stderr reminder of this every run).

### 3. Handoff

The output is a candidate table (not a SKILL.md, not a harvest decision) passed to `license-compliance-check` (step 7) for candidates that might use real code/patterns, or straight to `skill-creator` (step 3) with a "grounded in research X" note if it's purely methodology reference material (no code to license-check).

## Bundled files

- `scripts/github_scout.py` — wraps `gh api`/`gh search`, stdlib only, requires the `gh` CLI.
- `scripts/pypi_license_check.py` — wraps the PyPI JSON API license lookup, stdlib only (urllib).

## What scout-harvester does NOT do

- Doesn't decide SAFE/BLOCKED on licenses itself — always hands off to license-compliance-check.
- Doesn't write SKILL.md itself — that's skill-creator.
- Doesn't deeply investigate each candidate (reading all the source, testing every feature) — that's the next step's job if a candidate is selected to continue.

## Real cases run (2026-07-26)

| Need | Candidates found | Chosen | Handed off to |
| --- | --- | --- | --- |
| Parse PDF/DOCX/images → AI-optimized structure | Docling, MinerU, unstructured.io, marker, MarkItDown, LlamaParse, Reducto | Docling (MIT, self-hosted, strong JSON output) | license-compliance-check (cleared) → used as a dependency, no code copied |
| Bootstrap Python without an existing Python install | `uv` (Astral) | `uv` | license-compliance-check (MIT, used as an external tool via its official installer, no vendored code) |
| Reference structure for skill-creator | github.com/anthropics/skills | skill-creator (Apache-2.0) inside that repo; docx/pdf/pptx/xlsx BLOCKED | license-compliance-check (run for real, found mixed licensing) |
| Validating `github_scout.py`/`pypi_license_check.py` themselves | mermaid-js/mermaid (repo), python-docx/google-genai/openpyxl (PyPI) | Both scripts reproduced the same stars/license figures found manually earlier in the session | Confirms the scripts are safe to rely on going forward instead of hand-typing `gh api`/PyPI curl calls |
