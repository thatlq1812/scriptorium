# Decisions Pending — Scriptorium

No open architectural decisions right now.

Three prior entries were decided by the owner on 2026-07-26:
1. Next meta-skill: `elicit-tacit-process` — OK, per recommendation.
2. AI backend for quality-eval: the question had a wrong premise — Scriptorium **has no plan to integrate any AI backend** (including Elixverse). The product is a pure skill artifact; whichever agent runs a skill uses its own backend/model. Fixed in `docs/specs/STRATEGY_SPEC.md` §2 and §6.
3. Adversarial-input pass in `quality-eval`: **build it, don't run stage 4 yet.** After the v0.2.0 hardening round found 17 defects the existing stage-4 design would not have caught, the recommendation was to add a contract-conformance pass before stage 4's first run. Owner approved adding it and explicitly kept stage 4 unrun for now. Built as `quality-eval` v0.2.0 Pass A; no skill has been evaluated. A later session must not start running stage 4 without asking.

Add a new entry when a real architectural fork needs owner confirmation before proceeding. Fixed format: question → recommendation + reasoning → action plan → `Decision: [ ] OK / [ ] Override: ___`.
