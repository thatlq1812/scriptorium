# Master Context — Scriptorium

| Version | Date | Author | Description |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-26 | Claude | First version, written alongside setting up the project's documentation convention (referencing `D:/elix/platform`'s docs structure). |
| 1.1.0 | 2026-07-26 | Claude | Translated to English per thatlq1812 directive: the whole system (excluding `docs/archive/` and content brought in from outside) must be in English. Refreshed stale references (`ROADMAP.md` now exists). |
| 1.2.0 | 2026-07-26 | Claude | Added `outside_research/` as a recognized input directory (thatlq1812-authored active research on verticals/audiences, distilled into `docs/specs/`+`docs/ROADMAP.md`, kept verbatim like `docs/archive/` but living rather than frozen). See `docs/ROADMAP.md` §"Audience-tier expansion model" and `docs/specs/STRATEGY_SPEC.md` §5. |
| 1.3.0 | 2026-07-27 | Claude | Added `docs/templates/` (reusable operational templates, e.g. `CLUSTER_SURVEY_TEMPLATE.md`) and `outside_agy/` (external LegalTech reference material surveyed via a cross-agent `request.md` discussion) to the repo structure diagram — both existed on disk already this session, diagram was stale. |
| 1.4.0 | 2026-07-29 | Claude | Registry grew 39→62 skills in one session (`UPGRADE_PLAN_20260729.md`, full detail in `docs/STATUS.md`). Added `docs/guides/` (non-technical end-user documentation) and the repo-root `UPGRADE_PLAN_20260729.md` (active execution checklist) to the structure diagram — both new this session. Corrected §4's stated `DECISIONS_PENDING.md` convention ("remove an entry once decided") to match actual practice, which has kept a dated "Resolved" section for audit-trail purposes since before this session, not deleted resolved entries — the doc was already stale against real usage, not a new decision. |
| 1.5.0 | 2026-08-01 | Claude | `UPGRADE_PLAN_20260729.md` fully executed (all 7 items done) — archived to `docs/archive/upgrade-plan-2026-07-29/` alongside `request.md`, removed from the structure diagram and `CLAUDE.md`'s read order. Its still-live "scout before a new skill type" working rule was extracted into `CLAUDE.md`'s pipeline section (a standing rule, not tied to one execution round) before archiving, so it isn't lost. Added repo-root `SKILLS_MAP.md` (Mermaid registry overview) to the structure diagram. |
| 1.6.0 | 2026-08-01 | Claude | Registry grew 62→63 skills: `slide-deck-composer` (clone-and-inject `.pptx` generation from a caller-supplied real template), built and then upgraded twice more the same day (v0.1.0→v0.1.1 bug-fix round, v0.1.1→v0.2.0 thumbnail-grid/image-injection round) — full detail in `docs/STATUS.md`'s 2026-08-01 entries. Added gitignored `data/` (local dev/test fixtures, e.g. real Slidesgo templates — never bundled into a skill's shipped assets) to the structure diagram. |
| 1.7.0 | 2026-08-08 | Claude | Registry grew 63→73 across several sessions (full detail in `docs/STATUS.md`'s 2026-08-05 through 2026-08-08 entries, not repeated here): the GenVid media cluster (8 skills — Gemini image/video/audio generation, identity/style anchor profiles, ffmpeg-based assembly) transferred in 63→70; `personal-style-library` (70→71, a personal color-palette/style-sample catalog under `personal/`, composing into `media-anchor-profile`); the Light Design cluster's SVG/Pillow render backend (`svg-poster-builder`+`poster-generator`) superseded by `html-poster-composer` (71→72, real HTML/CSS via headless Chromium — auto-fit text measurement, font embedding, anchor-relative zone positioning, a circular seal/badge composer, and a general-purpose multi-page batch mode) — both superseded skills marked `operational_status: superseded` in the registry (a new state added to `registry/SCHEMA.md` alongside `paused`), left in place not deleted; `scriptorium-updater` (72→73, keeps a tester's local skill copies synced against this repo's own public GitHub remote during the current pre-commercial dev/test phase, add/update-only, never deletes). |
| 1.8.0 | 2026-08-13 | Claude | thatlq1812-directed restructuring, 2 of 2 items from a reviewed Gemini proposal (`STRATEGY_01.md`, full review in `docs/STATUS.md`): (1) 5 bootstrap skills merged into `toolchain-bootstrap` (74→75, see `docs/STATUS.md`'s "(cont'd 2)" entry for the full review/rejection of the proposal's broader 74-to-14 merge). (2) `skills/` reorganized from flat `skills/<skill_id>/` into `skills/<domain>/<skill_id>/` (general/education/meta/media/legal, matching registry `tags.domain` exactly — no new taxonomy invented) for easier manual browsing. Every cross-skill path assumption in the repo updated and re-verified for real: all `parents[N]` repo-root computations (+1 depth), all hardcoded cross-skill `sys.path` imports (converted to a domain-agnostic one-level glob lookup, since a sibling skill can now live in a different domain folder than the caller), `skill-exporter`'s 3 scripts (bundles still export flat `skills/<skill_id>/`, since a consuming harness has no concept of this repo's internal domain taxonomy), `scriptorium-updater`'s 3 scripts (auto-detects flat-vs-nested source layout for the transition period where the local clone may be reorganized before the public GitHub remote is), and `skill-creator`'s `scaffold_skill.py` (`--domain` now required, refuses a skill_id that already exists under any domain). Structure diagram updated in this file and `CLAUDE.md`. |
| 1.9.0 | 2026-08-13 | Claude | 2 more thatlq1812-directed items same day: (1) `gemini-generator` (74→75) merges `image-generator-gemini`/`video-generator-gemini`/`audio-generator-gemini` into one BYOK skill covering all 3 modalities, part of a provider-based restructuring of media generators; `gpt-generator`/`claude-generator`/`normal-generator` scaffolded only (75→78, new `operational_status: "planned"` state, `registry/SCHEMA.md` updated), real build deferred. (2) All 10 `operational_status: superseded` skills (the 5 merged bootstrap skills, the 3 merged Gemini generators, plus `svg-poster-builder`/`poster-generator` from an earlier session) physically moved out of the active domain folders into a new flat `skills/archive/<skill_id>/` (no domain subfolder) so manual browsing of the 5 active domain folders isn't cluttered with dead skills — content unchanged, never deleted, same reversibility discipline `operational_status: superseded` already established. Verified this required zero code changes anywhere: every domain-aware script built during 1.8.0's reorg already resolves a sibling skill via a one-level glob fallback when the registry-declared domain doesn't match a real on-disk path, so `skill-exporter`'s refusal, `scaffold_skill.py`'s cross-location duplicate detection, and `validate_skill.py` all continued working correctly against the new `archive/` location without modification -- confirmed by actually re-running each. Structure diagram updated in this file and `CLAUDE.md`. |
| 1.10.0 | 2026-08-13 | Claude | thatlq1812 directed splitting 2 of the 5 domain folders further, still same day: `general` (26 skills before archiving) → `general`/`office`/`design`, `education` (25 skills) → `education`/`academic`. Classification grounded in already-existing data, no new taxonomy invented: `office`/`design` split by real functional shape (document/diagram production vs. visual-brand-identity tools); `education`/`academic` split along `docs/specs/STRATEGY_SPEC.md` §5.1's own already-documented audience-tier ladder (academic = TA/Graduate + Lecturer/Researcher tiers; education = the remaining K12/Teacher/Parent/Lifelong-Learner tiers). 16 skills moved (5 to `office`, 4 to `design`, 7 to `academic`) via `git mv` + a registry `tags.domain` update; the same domain-agnostic glob-fallback mechanism from 1.8.0/1.9.0 meant zero script changes were needed, only a mechanical path-reference rewrite pass (6 files had a literal old-domain-qualified path string). Now 8 domain folders total: `general`/`office`/`design`/`education`/`academic`/`meta`/`media`/`legal`, plus the non-domain `archive/`. Verified real: full registry-vs-disk path check (all 78 skills at their expected path), `validate_skill.py` clean, a real cross-domain export (`slide-deck-composer` → `toolchain-bootstrap`, now `office`→`general`) and a real cross-domain scaffold duplicate-refusal both re-confirmed working. Structure diagram updated in this file and `CLAUDE.md`. |
| 1.11.0 | 2026-08-13 | Claude | thatlq1812 directed actively chaining `office-doc-creator` (VN-tailored, MIT-safe creation) into `docx` (editing/redlining/validation, the accepted-risk skill from 1.11.0) — real code change this round, not just documentation (see `docs/STATUS.md`'s "(cont'd 12)" entry for full detail). Building and running a real end-to-end test through the chain (a Vietnamese-diacritics `.docx` created by `office-doc-creator`, validated by `docx`) caught 2 real bugs neither skill's own isolated testing had ever surfaced: `docx`'s XSD validator silently broke on non-cp1252 content on Windows (a missing `encoding=` on a file open, fixed to binary-mode), and `office-doc-creator`'s `docx_numbering.py` had a real OOXML `CT_Lvl` schema-order bug (`w:lvlRestart`/`w:numFmt` swapped, fixed). Both `SKILL.md`s cross-documented ("Chains into `docx`" / "Chains from `office-doc-creator`"), both registry entries version-bumped and re-audited, `office-doc-creator`'s `dependencies` now lists `docx`. `docs/DECISIONS_PENDING.md` item 13 gained an addendum: this moves the accepted license-risk content from dormant to an active production dependency, thatlq1812-confirmed. Full registry re-swept via `validate_skill.py`: 7 pre-existing invalids unchanged, none new. |

---

## Quick Summary

| Property | Value |
| --- | --- |
| **Project Name** | Scriptorium (`elix/scriptorium`) |
| **Project Type** | System for creating / quality-evaluating / security-auditing / cataloging portable Agent Skills |
| **Core Philosophy** | Skill-first, no harness-building. Elicit → research → skill-creator → quality eval → security audit → registry, order not negotiable. |
| **Primary focus** | Vietnamese domain-specific workflows & cross-industry portable skills. |
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
│   ├── DECISIONS_PENDING.md    # Architectural decisions awaiting thatlq1812 confirmation
│   ├── ROADMAP.md              # Skill-expansion backlog
│   ├── specs/                  # Official specs — current source of truth
│   │   └── STRATEGY_SPEC.md
│   ├── templates/               # Reusable operational templates (e.g. CLUSTER_SURVEY_TEMPLATE.md)
│   ├── guides/                  # Non-technical end-user documentation (e.g. NON_TECH_USER_GUIDE.md)
│   └── archive/                # History, not current state — see archive/README.md
├── outside_research/           # thatlq1812-authored active research (surveys, external AI analysis)
│                                # on verticals/audiences — living input, kept verbatim (like
│                                # docs/archive/), distilled into docs/specs/ + docs/ROADMAP.md
├── outside_agy/                 # External LegalTech reference material (playbooks/skill models
│                                # from other products), comparison only, not copied
├── data/                        # Gitignored local fixtures (e.g. real Slidesgo .pptx templates for
│                                # slide-deck-composer's own dev/test use) — never bundled into a
│                                # skill's shipped assets, never a source of truth
├── skills/
│   └── <domain>/<skill_id>/SKILL.md  # Each skill is its own subfolder under a domain folder
│                                # (general/office/design/education/academic/meta/media/legal,
│                                # matches registry tags.domain; domain-per-folder reorg 2026-08-13,
│                                # split further into office/design/academic same day)
│   └── archive/<skill_id>/     # operational_status: superseded skills (flat, no domain
│                                # subfolder) — content unchanged, never deleted
├── registry/
│   ├── SCHEMA.md                # Multi-axis registry schema
│   └── skills.json              # Registry data
└── .venv/                      # Shared Python venv for all Python-dependent skills (gitignored, never committed)
```

## 4. Documentation convention

Directly referenced from how `D:/elix/platform/docs/` operates (README nav hub, versioned header table, `DECISIONS_PENDING.md` in a fixed format, dated archive on pivots), applied to Scriptorium at a smaller scale:

- **Every "current" doc (`MASTER_CONTEXT.md`, `STATUS.md`, `DECISIONS_PENDING.md`, every file in `specs/`) carries a version header table at the top** — Version/Date/Author/Description. Bump the version on any meaningful content change; never edit silently.
- **Real code/skills beat docs when they conflict.** `STATUS.md` must be verifiable against `registry/skills.json` + `skills/` — never written from memory or intent.
- **`docs/archive/` is history, not a current source of truth.** When a major distillation round happens (like research → STRATEGY_SPEC), raw discussion/research files move into a date-named subfolder (`pre-spec-YYYY-MM-DD/`), content unchanged.
- **`outside_research/` (repo root) is a living input, not history.** Unlike `docs/archive/`, it keeps growing — thatlq1812-authored surveys and external AI-assisted analysis about a candidate audience/vertical, gathered *before* a tier is built. Kept verbatim (original language, unedited) the same way `docs/archive/` is; insights get distilled into `docs/ROADMAP.md`/`docs/specs/STRATEGY_SPEC.md`, but the raw file itself is never treated as a source of truth on its own — and its brainstormed skill lists are candidate ideation, not elicited input (principle 4, `docs/specs/STRATEGY_SPEC.md` §7) — a real survey/interview or a real deployed prior system is still required before `skill-creator` runs for that audience.
- **`DECISIONS_PENDING.md`** uses exactly one format per entry: question → recommendation + reasoning → action plan → `Decision: [ ] OK / [ ] Override: ___`. An open (undecided) entry stays under `## Open`; once thatlq1812 decides, move it under `## Resolved` with the decision recorded — this is a dated audit trail of what was actually decided and why, not a to-do list to delete from once cleared.
- **The entire system must be in English**, except `docs/archive/` (historical discussion, kept verbatim in its original language) and content brought in from outside purely for reference. Optimizes for both AI and human readers — a user can still discuss with the agent in any language and the skill still works well.

## 5. Language policy

thatlq1812 directive (2026-07-26): the whole system must be English — every `SKILL.md`, every doc under `docs/` (except `archive/`), `registry/` content, and every script (docstrings, comments, print/error strings). Rationale: optimal for AI consumption and for users regardless of what language they converse in with the agent. `docs/archive/` stays in its original language as an unaltered historical record; external reference material brought in for context also keeps its original language.
