# Documentation — Scriptorium

Navigation hub. Read `MASTER_CONTEXT.md` first if you're new to the project.

## Read in this order

1. [MASTER_CONTEXT.md](MASTER_CONTEXT.md) — what Scriptorium is, repo structure, documentation convention.
2. [STATUS.md](STATUS.md) — real current status (which skills exist, which stages aren't built yet), verified against `registry/skills.json`.
3. [DECISIONS_PENDING.md](DECISIONS_PENDING.md) — architectural decisions awaiting owner confirmation before proceeding.
4. [specs/STRATEGY_SPEC.md](specs/STRATEGY_SPEC.md) — source of truth for strategic direction, pipeline, taxonomy, legal vertical, Elixverse gate.
5. [ROADMAP.md](ROADMAP.md) — skill-expansion backlog (external sources already license-verified, execution order).

## Directories

| Path | Content |
| --- | --- |
| `specs/` | Official, active specs. Write a new spec here when a decision/feature is big enough to distill into a source of truth. |
| `archive/` | History — discussion transcripts, raw research already distilled into `specs/`. See `archive/README.md`. Don't cite figures/decisions directly from here if `specs/` already has a corrected version. |
| `../outside_research/` (repo root) | Living input — owner-authored surveys and external AI-assisted analysis on candidate audiences/verticals, gathered before a tier is built. Distilled into `ROADMAP.md`/`specs/STRATEGY_SPEC.md`; its brainstormed skill lists are ideation only, not elicited input. |

## Rule when things conflict

`skills/` and `registry/` (real code/skills) beat every doc. Within docs, `specs/` beats `archive/`. `STATUS.md` must be verifiable against `registry/skills.json` — if they diverge, fix `STATUS.md`, not the registry, to match the doc.
