---
name: personal-memory-log
description: Local-only, append-only memory log for this workspace owner -- freeform observations (who the user is, preferences, daily habits, ongoing context) that don't fit personal-profile-manager's fixed identity/organization/contact schema. init_memory.py scaffolds personal/memory/ plus an index MEMORY.md; write_memory.py appends one dated entry (its own slug.md file, tagged user/feedback/project/reference) and keeps the index line for that entry in sync (updates in place on a re-run with --force, never duplicates). Use when a task surfaces a durable fact about the user that isn't identity/org/contact data -- a preference, a working habit, context behind an ongoing project, a correction the agent should apply from now on. Do NOT use for identity/organization/contact fields (that's personal-profile-manager's job) and do NOT use for a single-turn detail with no future relevance.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (argparse, re, pathlib) -- no dependency, no venv needed, local-only, zero network calls. Verified running clean: Claude Code (2026-08-20).'
metadata:
  domain: general
  task_type: coordination
  risk_tier: N2
  source: self-authored
  elicited_from: "thatlq1812 direction 2026-08-20 (PROJECT.md): personal/ should cover not just identity/org data but also user preferences, daily habits/work patterns -- \"nói chung là 'ghi nhớ' để agent dễ dàng hiểu rõ người dùng là ai, thế nào, cần gì, muốn gì... Memory chủ động tối ưu ấy\" -- explicitly distinct from personal-profile-manager's validated identity schema, since that skill's own scope is deliberately fixed (identity/organization/contact only) and its style-adaptation half only ever proposes a change, never logs a running memory. Structure (one dated entry per file, tagged user/feedback/project/reference, plus a MEMORY.md index of one-line hooks) is a direct, deliberate port of the memory mechanism already specified for this app's own Claude Code harness (the file+index shape, the 4-way type taxonomy, the ~150-char index-line cap, the 'write from confirmation and correction, not just explicit save requests' discipline) -- a real, already-deployed mechanism, not invented from scratch. thatlq1812 confirmed reusing that exact taxonomy for this workspace's own agent (2026-08-20, same thread: \"Xác nhận có\")."
  version: 0.1.0
  changelog_0_1_0: "Initial version. init_memory.py (scaffold personal/memory/ + MEMORY.md index, --force-gated re-init) and write_memory.py (append or, with --force, update one entry -- frontmatter file + synced index line, index line truncated to a 150-char budget) verified running clean, all real (see Verified below)."
  grounding: not_applicable
  object_type: ["memory-entry"]
---

# personal-memory-log

A local, append-only memory log for this workspace's owner -- freeform observations an agent picks up over time (preferences, habits, recurring context) that `personal-profile-manager`'s fixed identity/organization/contact schema was never meant to hold.

## Why this skill, and why this scope

`personal-profile-manager`'s `personal/profile.json` is a validated schema for a fixed set of facts (identity, organization, contact, optionally an issuing-organization's letterhead identity) -- exactly the shape a form-filling skill needs, and deliberately not a place for a growing, freeform "here's what I've learned about this user" log. Its own style-adaptation half (`propose_style_update.py`) is the closest existing mechanism, but it only ever turns a feedback log into a one-time PROPOSED instruction-update block for human review -- it does not keep a running memory an agent reads back at the start of every session.

This skill fills that specific gap: a running log the agent reads proactively (referenced from this workspace's own `AGENTS.md`, the way `personal/profile.json` already is) and writes to proactively, not only when the user explicitly says "remember this."

## What belongs in a memory entry, and what doesn't

Same discipline as the memory mechanism this is ported from -- write from what was actually said or actually happened, never from inference or a guess:

- **user** -- the workspace owner's role, goals, responsibilities, domain knowledge (e.g. "lawyer, drafts labor contracts, prefers Vietnamese with English technical terms").
- **feedback** -- guidance on how to approach work, from a correction OR a confirmation of something that worked (e.g. "don't scaffold a project for a one-off translation request -- corrected 2026-08-20").
- **project** -- ongoing work context not otherwise derivable from the files themselves (who's doing what, why, by when -- convert relative dates to absolute ones before writing).
- **reference** -- pointers to where information lives in an external system (e.g. "case files older than 2024 are tracked in the firm's DMS, not this workspace").

Does NOT belong here: identity/organization/contact fields (`personal-profile-manager`), anything already derivable by reading the workspace's own files, or a detail with no relevance beyond the current turn.

## Run

```bash
python scripts/init_memory.py personal/memory
python scripts/write_memory.py personal/memory --name <slug> --type <user|feedback|project|reference> \
    --description "<one-line summary>" --body "<entry content>"
```

`init_memory.py` creates `personal/memory/` and its `MEMORY.md` index (a fixed header, no entries yet); refuses if `MEMORY.md` already exists, unless `--force` (same convention as `personal-profile-manager`'s `init_profile.py`). Run once per workspace, lazily -- the first time the agent has something worth remembering, not upfront.

`write_memory.py` writes `personal/memory/<name>.md` (6-key-style frontmatter: `name`, `description`, `metadata.type`, then the body) and updates exactly one line in `MEMORY.md` for that entry -- appended if new, replaced in place if `--name` already has an entry and `--force` is given (never duplicated). `--name` must be lowercase kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`); `--type` must be exactly one of `user`/`feedback`/`project`/`reference`, refused otherwise. Body content is required via `--body <text>` or `--body-file <path>` (exactly one, not both) -- an empty body is refused. The index line is `- [<name>](<name>.md) — <description>`, truncated (with a trailing `...`) if the whole line would exceed 150 characters, so `MEMORY.md` stays scannable as entries accumulate.

Exit codes (both scripts): 0 = written, 1 = refused due to existing state without `--force`, 2 = bad arguments/malformed input.

## What this skill does NOT do

- Does not touch `personal/profile.json` or any of `personal-profile-manager`'s files -- fully independent store, same `personal/` parent directory only because both are per-workspace-owner local data.
- Does not prune, summarize, or auto-delete old entries -- `MEMORY.md` growing past a readable length (past ~200 lines) is a signal to the agent to consolidate/tidy by hand, not something either script does automatically.
- Does not do fuzzy matching or search -- consulting memory means reading `MEMORY.md` (and the linked entry files) directly, same as reading any other file in the workspace.
- Does not sync/back up anywhere -- purely local, same privacy posture as `personal/profile.json` (see Privacy below).
- Does not call any LLM/AI API -- pure local file I/O.

## Privacy

Lives under `personal/`, which `.gitignore` already excludes by default (see `personal-profile-manager/SKILL.md`'s own "Privacy" section) -- a `personal/memory/` directory never gets committed even in a repo the user later makes public, same as `profile.json`.

## Verified

`init_memory.py`: fresh scaffold created `personal/memory/MEMORY.md` with the fixed header; re-running without `--force` against the same path correctly refused (exit 1); nonexistent parent directories were created automatically.

`write_memory.py`: two real entries written (`user` and `feedback` type) -- both `<slug>.md` files and their `MEMORY.md` index lines created correctly, in the order written. Re-running the same `--name` without `--force` correctly refused (exit 1, entry file named). An invalid `--type` (`wrong`) correctly refused by argparse's own choices check (exit 2). An invalid `--name` (`"Bad Slug!"`, uppercase + space) correctly refused (exit 2, naming the required regex). Re-running the same `--name` WITH `--force` correctly updated the entry file's content AND replaced its existing `MEMORY.md` index line in place (verified: no duplicate line for the same entry after the update). Passing both `--body` and `--body-file` together correctly refused (exit 2); passing neither would also be refused by the same check. Running against a `memory_dir` that was never initialized (no `init_memory.py` run) correctly refused (exit 1, telling the caller to run `init_memory.py` first). A deliberately long `--description` (>150 chars once composed with the entry's own `- [name](name.md) — ` prefix) was correctly truncated to exactly 150 characters with a trailing `...`, confirmed by measuring the real written line length.

## Known limitations (v0.1.0)

- Not yet through quality-eval (stage 4) or security-audit (stage 5) -- see `registry/skills.json`'s entry for this skill's current `quality_score`/`security_audit` status before treating it as production-ready.
- Only verified running directly via `python` in this repo's dev environment, not yet exercised end-to-end through the app's actual kimi-code engine inside a real workspace (`.venv`/shared-Python-path considerations that apply to every other skill in this registry apply here too, untested for this one specifically).
- No migration story if the entry frontmatter shape changes in a later version -- an existing `personal/memory/<name>.md` from an older version isn't automatically upgraded.
