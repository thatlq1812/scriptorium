# Decisions Pending — Scriptorium

No open architectural decisions right now.

Two prior entries (next meta-skill, AI backend for quality-eval) were decided by the owner on 2026-07-26:
1. Next meta-skill: `elicit-tacit-process` — OK, per recommendation.
2. AI backend for quality-eval: the question had a wrong premise — Scriptorium **has no plan to integrate any AI backend** (including Elixverse). The product is a pure skill artifact; whichever agent runs a skill uses its own backend/model. Fixed in `docs/specs/STRATEGY_SPEC.md` §2 and §6.

Add a new entry when a real architectural fork needs owner confirmation before proceeding. Fixed format: question → recommendation + reasoning → action plan → `Decision: [ ] OK / [ ] Override: ___`.
