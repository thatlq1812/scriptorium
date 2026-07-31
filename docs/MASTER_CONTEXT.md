# Master Context — Scriptorium

| Version | Date | Author | Description |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-26 | Claude | First version, written alongside setting up the project's documentation convention (referencing `D:/elix/platform`'s docs structure). |
| 1.1.0 | 2026-07-26 | Claude | Translated to English per owner directive: the whole system (excluding `docs/archive/` and content brought in from outside) must be in English. Refreshed stale references (`ROADMAP.md` now exists). |
| 1.2.0 | 2026-07-26 | Claude | Added `outside_research/` as a recognized input directory (owner-authored active research on verticals/audiences, distilled into `docs/specs/`+`docs/ROADMAP.md`, kept verbatim like `docs/archive/` but living rather than frozen). See `docs/ROADMAP.md` §"Audience-tier expansion model" and `docs/specs/STRATEGY_SPEC.md` §5. |
| 1.3.0 | 2026-07-27 | Claude | Added `docs/templates/` (reusable operational templates, e.g. `CLUSTER_SURVEY_TEMPLATE.md`) and `outside_agy/` (external LegalTech reference material surveyed via a cross-agent `request.md` discussion) to the repo structure diagram — both existed on disk already this session, diagram was stale. |
| 1.4.0 | 2026-07-29 | Claude | Registry grew 39→62 skills in one session (`UPGRADE_PLAN_20260729.md`, full detail in `docs/STATUS.md`). Added `docs/guides/` (non-technical end-user documentation) and the repo-root `UPGRADE_PLAN_20260729.md` (active execution checklist) to the structure diagram — both new this session. Corrected §4's stated `DECISIONS_PENDING.md` convention ("remove an entry once decided") to match actual practice, which has kept a dated "Resolved" section for audit-trail purposes since before this session, not deleted resolved entries — the doc was already stale against real usage, not a new decision. |
| 1.5.0 | 2026-08-01 | Claude | `UPGRADE_PLAN_20260729.md` fully executed (all 7 items done) — archived to `docs/archive/upgrade-plan-2026-07-29/` alongside `request.md`, removed from the structure diagram and `CLAUDE.md`'s read order. Its still-live "scout before a new skill type" working rule was extracted into `CLAUDE.md`'s pipeline section (a standing rule, not tied to one execution round) before archiving, so it isn't lost. Added repo-root `SKILLS_MAP.md` (Mermaid registry overview) to the structure diagram. |

---

## Quick Summary

| Property | Value |
| --- | --- |
| **Project Name** | Scriptorium (`elix/scriptorium`) |
| **Project Type** | System for creating / quality-evaluating / security-auditing / cataloging portable Agent Skills |
| **Core Philosophy** | Skill-first, no harness-building. Elicit → research → skill-creator → quality eval → security audit → registry, order not negotiable. |
| **Predecessor** | EduStation (`D:/elix/edustation`) — pivoted due to governance-before-traction, not a flawed architecture. See `docs/specs/STRATEGY_SPEC.md` §1. |
| **Pilot vertical** | Vietnamese legal — positioned at the meta layer (producing + auditing skills), not a legal-lookup chatbot. |
| **AI backend** | None, by design — Scriptorium never calls any AI API; skill artifacts run on the consuming agent's own backend. See `docs/specs/STRATEGY_SPEC.md` §2, §6. |

---

## 1. What's being built (current)

A 9-step pipeline and the set of meta-skills that operate it (see `docs/specs/STRATEGY_SPEC.md` §3 for the status of each step). The tangible output of each step is:

- One or more `SKILL.md` files under `skills/<skill_id>/`, matching the agentskills.io 6-field spec.
- An entry in `registry/skills.json`, matching the `registry/SCHEMA.md` schema.

## 2. What we are NOT building

- No dedicated app/CLI/harness — skills run on the existing ecosystem (~44 platforms supported Agent Skills as of mid-2026).
- No manifest outside the agentskills.io spec — project-specific fields always live inside frontmatter `metadata`.
- No merging quality evaluation and security audit into one step.

## 3. Repo structure

```
scriptorium/
├── README.md                  # Entry point — summary + pointer into docs/
├── docs/
│   ├── README.md               # Navigation hub (read this first)
│   ├── MASTER_CONTEXT.md       # This file — architecture & scope
│   ├── STATUS.md               # Real status, verified against skills/ + registry/
│   ├── DECISIONS_PENDING.md    # Architectural decisions awaiting owner confirmation
│   ├── ROADMAP.md              # Skill-expansion backlog
│   ├── specs/                  # Official specs — current source of truth
│   │   └── STRATEGY_SPEC.md
│   ├── templates/               # Reusable operational templates (e.g. CLUSTER_SURVEY_TEMPLATE.md)
│   ├── guides/                  # Non-technical end-user documentation (e.g. NON_TECH_USER_GUIDE.md)
│   └── archive/                # History, not current state — see archive/README.md
├── outside_research/           # Owner-authored active research (surveys, external AI analysis)
│                                # on verticals/audiences — living input, kept verbatim (like
│                                # docs/archive/), distilled into docs/specs/ + docs/ROADMAP.md
├── outside_agy/                 # External LegalTech reference material (playbooks/skill models
│                                # from other products), comparison only, not copied
├── skills/
│   └── <skill_id>/SKILL.md     # Each skill is its own subfolder
├── registry/
│   ├── SCHEMA.md                # Multi-axis registry schema
│   └── skills.json              # Registry data
├── SKILLS_MAP.md                # Mermaid overview of the registry (repo root, snapshot)
└── .venv/                      # Shared Python venv for all Python-dependent skills (gitignored, never committed)
```

## 4. Documentation convention

Directly referenced from how `D:/elix/platform/docs/` operates (README nav hub, versioned header table, `DECISIONS_PENDING.md` in a fixed format, dated archive on pivots), applied to Scriptorium at a smaller scale:

- **Every "current" doc (`MASTER_CONTEXT.md`, `STATUS.md`, `DECISIONS_PENDING.md`, every file in `specs/`) carries a version header table at the top** — Version/Date/Author/Description. Bump the version on any meaningful content change; never edit silently.
- **Real code/skills beat docs when they conflict.** `STATUS.md` must be verifiable against `registry/skills.json` + `skills/` — never written from memory or intent.
- **`docs/archive/` is history, not a current source of truth.** When a major distillation round happens (like research → STRATEGY_SPEC), raw discussion/research files move into a date-named subfolder (`pre-spec-YYYY-MM-DD/`), content unchanged.
- **`outside_research/` (repo root) is a living input, not history.** Unlike `docs/archive/`, it keeps growing — owner-authored surveys and external AI-assisted analysis about a candidate audience/vertical, gathered *before* a tier is built. Kept verbatim (original language, unedited) the same way `docs/archive/` is; insights get distilled into `docs/ROADMAP.md`/`docs/specs/STRATEGY_SPEC.md`, but the raw file itself is never treated as a source of truth on its own — and its brainstormed skill lists are candidate ideation, not elicited input (principle 4, `docs/specs/STRATEGY_SPEC.md` §7) — a real survey/interview or a real deployed prior system is still required before `skill-creator` runs for that audience.
- **`DECISIONS_PENDING.md`** uses exactly one format per entry: question → recommendation + reasoning → action plan → `Decision: [ ] OK / [ ] Override: ___`. An open (undecided) entry stays under `## Open`; once the owner decides, move it under `## Resolved` with the decision recorded — this is a dated audit trail of what was actually decided and why, not a to-do list to delete from once cleared.
- **The entire system must be in English**, except `docs/archive/` (historical discussion, kept verbatim in its original language) and content brought in from outside purely for reference. Optimizes for both AI and human readers — a user can still discuss with the agent in any language and the skill still works well.

## 5. Language policy

Owner directive (2026-07-26): the whole system must be English — every `SKILL.md`, every doc under `docs/` (except `archive/`), `registry/` content, and every script (docstrings, comments, print/error strings). Rationale: optimal for AI consumption and for users regardless of what language they converse in with the agent. `docs/archive/` stays in its original language as an unaltered historical record; external reference material brought in for context also keeps its original language.
