---
name: license-compliance-check
description: 'Determines the real license of a candidate skill/repo to harvest and decides go/no-go before that content touches skill-creator. Use right after the scout/harvester skill (step 6), mandatory before any harvested content becomes input to skill-creator (step 3) — no "internal reference only" exception. Do NOT use to draft a new skill yourself (that''s skill-creator) — this skill only answers one question: is this source allowed to be used, and to what extent.'
license: MIT
compatibility: 'A pure read-and-classify process, no dependency on a specific harness. Verified running clean: Claude Code (2026-07-26, applied for real to github.com/anthropics/skills via `gh api`).'
metadata:
  domain: meta
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited from a real case 2026-07-26: checked the license of github.com/anthropics/skills (used gh api to read each skill's LICENSE.txt + THIRD_PARTY_NOTICES.md directly) — found mixed licensing within a single repo, concrete evidence for why this step must be handled separately, never batch-guessed"
  version: 0.2.0
---

# license-compliance-check

Answers exactly 1 question per harvest candidate: **to what extent is this allowed to be used**. Never guess a license from the repo name, a general README, or "looks like open source" — always read the real license file.

## Why never batch-guess (real case, 2026-07-26)

`github.com/anthropics/skills` has no single root LICENSE covering the whole repo (`gh api repos/anthropics/skills --jq '.license'` returns empty). The README says "many skills... are open source (Apache 2.0)" — but `skills/pdf/LICENSE.txt` is an exclusive Anthropic clause, absolutely banning extract/copy/derive/distribute. Guessing "this repo is generally open" and harvesting `pdf/` too would be a real license violation. **Always read the license at the exact file/folder level of what you intend to harvest, never at the repo level.**

## Process

1. **Find the license file at the correct level.** Priority order: a license file inside the exact folder/skill to harvest (e.g. `skills/<x>/LICENSE.txt`) → the repo's root license file (`LICENSE`, `LICENSE.txt`, `COPYING`) → the `license` field in `package.json`/`pyproject.toml`/SKILL.md frontmatter → the GitHub API `repos/{owner}/{repo}` `license` field. Stop at the first level found — a more specific level always wins over a more general one (lesson from the anthropics/skills case).
2. **No license found anywhere** → default to **BLOCKED**. No license = the original author retains full rights under default copyright law, not "treat as free to use."
3. **Classify** the found license into 1 of 4 groups:
   - **Permissive** (MIT, Apache-2.0, BSD-2/3-Clause, ISC) → **SAFE**: allowed to adapt/harvest, keep attribution; if Apache-2.0, add a change-notice on modification (§4(b)).
   - **Copyleft** (any GPL/AGPL/LGPL version) → **BLOCKED for direct embedding** into a Scriptorium skill (MIT) — copyleft propagates open-source obligations. Only acceptable as a separate dependency/subprocess call (no static-linking, no code copying), and must be flagged for owner review case-by-case, never decided unilaterally.
   - **Source-available / proprietary with an explicit contractual clause banning redistribution** (like Anthropic's `pdf/LICENSE.txt` — bans "extract/copy/retain/derive/distribute") → **absolutely BLOCKED, not debt-eligible**. This differs in nature from "license unclear" — it's a specific contractual restriction; using `license_debt` to legitimize violating it would be wrong, the owner exception below does not apply.
   - **Ambiguous/no license file/unclear** → defaults to BLOCKED, but **the owner has authorized controlled "legal debt" during the bootstrap phase** (`docs/specs/STRATEGY_SPEC.md` §7 point 5, decision 2026-07-26): if the owner confirms wanting to use it despite the unclear license, record `license_debt` on the registry entry (`source`, `reason`, `remediation_plan`, `acknowledged_by: "owner"`, `date` — see `registry/SCHEMA.md`), add it to the debt ledger in `docs/STATUS.md`, and that skill must not be distributed/published externally while in debt. Never decide this on the owner's behalf — always ask before recording debt; this is a deliberate risk decision, not a default.
4. **Record provenance** for every decision: `{candidate, repo_url, path, commit, license_found, classification, decision, date}`. This feeds directly into the `source`/`license`/`license_debt` fields of `registry/skills.json` (see `registry/SCHEMA.md`).
5. If SAFE: hand off to the next step (dedup/novelty-check, step 8) before reaching skill-creator (step 3) — license-compliance-check never writes a SKILL.md itself.

## Output

A decision table (candidate → license → classification → SAFE/BLOCKED → reason), not a SKILL.md. Only SAFE candidates get passed further down the pipeline.

## Real case run (2026-07-26): `github.com/anthropics/skills`

| Candidate | License found | Classification | Decision |
| --- | --- | --- | --- |
| `skills/meta/skill-creator/` | Apache-2.0 (its own LICENSE.txt in the folder) | Permissive | **SAFE** — attribution + change-notice when adapting |
| `skills/pdf/`, `skills/docx/`, `skills/pptx/`, `skills/xlsx/` | Exclusive Anthropic clause (its own LICENSE.txt, bans extract/copy/derive/distribute) | Proprietary, no-redistribution | **Absolutely BLOCKED** |
| Other skills in `skills/` (mcp-builder, webapp-testing, frontend-design...) | Not checked individually yet — the README only says "many," not "all" | Not classified yet | **Undecided — needs individual checking before harvesting anything in this group** |
