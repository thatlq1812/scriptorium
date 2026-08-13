---
name: scriptorium-updater
description: Keeps a tester's own local copy of Scriptorium's `skills/` folder in sync with the real upstream repo (github.com/thatlq1812/scriptorium, public during the current dev/test phase), without re-downloading/re-exporting a bundle each time. `init_source_clone.py` does a one-time shallow clone into a caller-chosen directory. `check_updates.py` is read-only (`git fetch` + diff) -- reports whether the clone is behind and exactly which skill_ids changed version, never touching the working tree. `sync_skills.py` pulls the source (refuses on uncommitted local changes) then copies `skills/` into a caller-chosen destination (e.g. `.claude/skills/`, `.agents/skills/` -- not guessed) -- ADD/UPDATE ONLY, never deletes; a destination-only skill_id is reported, not removed, since deciding what that means is the calling agent's judgment call. Use when a tester wants local skill copies kept current. Do NOT use this to auto-apply updates silently -- every script prints a structured account of what changed/would change.
license: MIT
compatibility: 'Requires Python 3.11+, stdlib only (subprocess, shutil, json, pathlib) -- no dependency, no venv needed. Requires `git` on PATH. Network calls: `git clone`/`git fetch`/`git pull` against github.com only, no other network access. Verified running clean: Claude Code, Windows (2026-08-07, cold-agent-verified + stdin hang fixed 2026-08-08).'
metadata:
  domain: meta
  task_type: coordination
  risk_tier: N2
  source: self-authored
  elicited_from: "Owner direction (2026-08-07): during the current pre-commercial dev/test phase, the Scriptorium repo is deliberately public (confirmed via `gh repo view`: PUBLIC, not a stray misconfiguration -- owner's own words: 'hiện tại vẫn đang trong giai đoạn phát triển, nên chưa cần set private, và tôi muốn hệ thống có thể cập nhật cho tester mà không cần phải tải đi tải lại skill'). Design explicitly follows this registry's own established 2-step bootstrap discipline (toolchain-bootstrap/browser-web-renderer: detect safely by default, apply only as a separate explicit step) rather than a fully-automatic silent updater, which the owner's own framing ruled out directly: 'không phải chạy cơ học không đâu, mà do agent làm theo ghi chú' -- this skill's job ends at producing an accurate report; a destination-only skill_id (present locally, absent upstream) is never auto-deleted, the calling agent decides what it means by reading the report, same discipline as `document-ai-structurer`'s propose-then-agent-reviews-then-mechanically-applies shape applied to sync instead of content structuring. The add/update-only (never delete) behavior was an explicit owner choice between 2 offered options, recorded here since it's a real, deliberate design decision, not a default. v0.1.1 (2026-08-08): owner directed an independent cold-agent verification round (a fresh subagent, its own scratch directory, no context from the building session) -- real, standard practice in this registry for a newly-built skill (matches slide-deck-composer's own v0.5.0 cold-agent round)."
  version: 0.1.1
  changelog_0_1_1: "Real bug found by a cold-agent test (2026-08-08): sync_skills.py's git pull hung indefinitely under a piped/non-interactive invocation -- inherited stdin let git's credential helper try to prompt and block forever, zero error message. Fixed by extracting the 3 scripts' near-duplicate _run_git helpers into one shared git_utils.run_git() with stdin=subprocess.DEVNULL set unconditionally (any credential prompt now fails fast and loud instead of hanging) -- the duplication itself is exactly the class of bug already found once this session (html-poster-composer's ZONE_BASE_CSS). Re-verified: the exact hanging invocation now completes in under 1 second; full 3-script regression confirmed unaffected."
  grounding: not_applicable
  object_type: []
---

# scriptorium-updater

Three scripts, three separate concerns -- clone once, check often (safe), sync explicitly (writes files, never deletes).

## Why this skill, and why this scope

Testers working with Scriptorium skills currently have no way to pick up new versions except re-downloading or re-exporting a bundle by hand each time something changes. Since the repo is deliberately public during this dev/test phase (not `skill-exporter`'s commercial retail-bundle path, which stays the distribution mechanism once the project leaves this phase), a direct git-backed sync is a real, low-friction option for testers specifically. This is NOT a general git-automation tool and does not touch `registry/skills.json`, `docs/`, or anything outside `skills/` -- a tester using skills directly only needs each skill's own self-contained `SKILL.md` (per the agentskills.io 6-field spec), not this project's internal bookkeeping.

## Run

### 1. Clone the source (once)

```bash
python scripts/init_source_clone.py <dest_dir>
```

Shallow-clones `github.com/thatlq1812/scriptorium` into `dest_dir` (refuses if it already exists and is non-empty). This becomes the "source" the other 2 scripts operate against -- treat it as a dedicated mirror, not a place to edit files yourself (`sync_skills.py` refuses to pull over uncommitted local changes in it).

### 2. Check for updates (safe, read-only, run this often)

```bash
python scripts/check_updates.py <source_repo_dir> [--branch origin/master]
```

`git fetch` (updates remote-tracking refs only) + diffs `registry/skills.json`'s `skill_id -> version` map between local `HEAD` and the target branch. Prints a JSON report: `up_to_date`, `local_commit`/`remote_commit`, `changed_skill_dirs` (any file under `skills/<id>/` differs), `version_changes` (`skill_id`/`local_version`/`remote_version` for every skill whose declared version actually differs). Never touches the working tree -- safe to run at the start of every session.

### 3. Sync into your own project (writes files -- add/update only, never deletes)

```bash
python scripts/sync_skills.py <source_repo_dir> <dest_skills_dir> [--dry-run]
```

Pulls the source clone (`--ff-only`; refuses if it has uncommitted local changes), then copies every `skills/<id>/` folder into `dest_skills_dir/<id>/` -- new skill_ids are added, existing ones are overwritten file-by-file (`shutil.copytree(..., dirs_exist_ok=True)`, which merges rather than replaces a directory, so an existing destination file with no source counterpart is left alone). Prints a JSON report: `added`, `updated` (with `old_version`/`new_version` per skill), `unchanged_count`, `destination_only` (skill_ids at the destination not present in this sync -- listed, never removed). `--dry-run` still pulls the source (safe, fast-forward-only) but skips the destination write, so the report reflects the real latest state without touching your project.

`dest_skills_dir` is whichever path your harness actually scans -- Claude Code: `.claude/skills/`, goose/ACP: `.agents/skills/`, Cursor: `.cursor/skills/` (see `skill-exporter`'s own "Where to install" convention; this script does not guess it, pass the real path).

## What this skill does NOT do

- Does not delete anything, ever -- a skill_id or file present at the destination but not in the source is reported (`destination_only`), never removed. Deciding what that means is the calling agent's call.
- Does not sync `registry/skills.json`, `docs/`, `personal/`, or anything outside `skills/` -- `personal/` in particular is a separate, per-user, gitignored mechanism (`personal-profile-manager`/`personal-style-library`) that has nothing to do with this skill and is never touched by it.
- Does not guess a harness's skill-install path -- the caller supplies the real `dest_skills_dir`.
- Does not run automatically on its own on any schedule or session-start hook -- this skill only provides the scripts; wiring `check_updates.py`/`sync_skills.py` into an actual per-session routine (if a tester wants that) is a harness/automation decision outside this skill's own scope.
- Does not replace `skill-exporter` for actual commercial distribution -- this is a dev/test-phase tester convenience specific to the repo being public right now, not the retail bundle path.

## Verified

Real end-to-end run against the real public repo (2026-08-07): `init_source_clone.py` cloned `github.com/thatlq1812/scriptorium` for real. `check_updates.py` against a fresh clone correctly reported `up_to_date: true`; after resetting the clone's local `HEAD` back 5 real commits (simulating a stale tester), correctly reported `up_to_date: false` with the exact 10 real `skill_id`s that changed and their real old/new versions (e.g. `image-generator-gemini: 0.3.0 -> 0.4.2`). `sync_skills.py --dry-run` against that stale clone correctly pulled the source to latest (dry-run only gates the destination write, not the source pull -- verified this distinction matters: pulling is what makes the report accurate) and reported the update without writing; the real (non-dry-run) sync then wrote 71 real skill folders, confirmed by direct inspection: a pre-seeded unrelated `my-own-test-skill` folder was left completely untouched, a pre-seeded stale `image-generator-gemini` was updated to its real new version while a pre-existing extra file inside that same folder (not part of the real skill) survived (add/update only, confirmed at the file level too, not just the top-level skill-folder level). 4 refusal paths verified real: uncommitted changes in the source clone (exit 1), source not a git repo (both scripts, exit 2), `init_source_clone.py` into a non-empty directory (exit 2). One real bug found and fixed during this verification: `git rev-parse` on an unresolvable branch ref exits non-zero but still echoes the raw argument text to stdout -- the initial check (`if not remote_head`) missed this since stdout wasn't actually empty; fixed by checking `returncode` explicitly instead of inferring failure from empty output.

**v0.1.1**: an independent cold-agent verification (a fresh subagent, no prior context, its own new scratch directory) reproduced every claim above for real and found ONE more real bug: `sync_skills.py`'s `git pull` hung indefinitely when invoked from a non-interactive/piped calling context (`... | tail -N`) -- `subprocess.run()` with no explicit `stdin` inherits the parent's stdin, and git's credential helper (Windows GCM in the reproduction) can try to prompt interactively on that inherited stdin and block forever with zero error message, the exact "silent hang" class this project refuses everywhere else. Fixed by extracting a single shared `git_utils.run_git()` (all 3 scripts previously had their own near-identical `_run_git` helper -- exactly the kind of duplication that already caused a real bug once this same session, see `html-poster-composer`'s `ZONE_BASE_CSS` note) with `stdin=subprocess.DEVNULL` set unconditionally, so any credential prompt fails fast and loudly instead of hanging. Re-verified: the exact piped invocation that hung during the cold-agent test now completes in under 1 second with correct output; full regression of `init_source_clone.py`/`check_updates.py`/`sync_skills.py --dry-run` confirmed unaffected.

## Known limitations (v0.1.1)

- `check_updates.py`'s `changed_skill_dirs` is a file-level diff (any file under a skill's folder differs) while `version_changes` is a declared-version diff -- the two can disagree (e.g. a doc-only SKILL.md edit that didn't bump `version:` still shows in `changed_skill_dirs` but not `version_changes`); both are reported for exactly this reason, neither alone is the full picture.
- No automatic conflict resolution beyond refusing outright -- if the source clone has uncommitted changes, the fix is manual (commit/stash/discard), this skill doesn't attempt to reconcile anything itself.
- This is a dev/test-phase mechanism tied to the repo currently being public; if/when the project moves to the stated commercial "sold retail, never given away" model, this skill's own premise needs revisiting (a private repo can't be `git clone`d by a tester the same way) -- flagged as a real, known future decision point, not resolved here.
