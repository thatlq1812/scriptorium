# Getting a Scriptorium Skill Pack Working — A Guide for Non-Technical Users

This guide is for someone who is **not** a programmer, but has an AI coding assistant (an "agent harness" like Claude Code) installed and wants to give it a set of Scriptorium skills to use — for example, a lawyer who wants their assistant to check contracts consistently, or a teacher who wants help building lesson plans the same way every time.

You will not need to write or edit any code. You only need to: ask for a bundle, unzip a file, and put a folder in the right place.

## What you're actually getting

A Scriptorium "skill" is a small folder of instructions (and sometimes small helper programs) that teaches your AI assistant how to do one specific task reliably — the same way every time, with built-in checks that catch mistakes. A "bundle" is a `.zip` file containing several skills chosen for your specific work, not the entire Scriptorium library.

**Only the skills you actually need are included — never a "full pack" dump.** This is deliberate: an assistant loaded with hundreds of irrelevant skills gets slower and more confused, not smarter, the same way a desk buried in unrelated paperwork slows you down even if the one document you need is somewhere in the pile.

## Step 1 — Ask for a bundle

Tell whoever is running Scriptorium for you (or, if you're doing it yourself, tell your own AI assistant while it's working inside the Scriptorium project) what you do and what you want help with. Plain language is fine — for example:

> "I'm a lawyer. I want help checking contracts for numbering mistakes and missing clauses, doing legal research write-ups, and filling out dossiers. Prepare me a skill pack for that."

The assistant will pick the matching skills from Scriptorium's catalog and build you a `.zip` file (using a tool called `skill-exporter`). You do not need to name skills by their technical id — describing your work is enough.

### A real example

Asking for exactly this produced a real bundle during this guide's own testing (2026-07-29): a 5-skill Legal starter pack (`contract-consistency-linter`, `legal-research-brief`, `legal-citation-checker`, `contract-risk-log`, `legal-form-filler`), plus 2 supporting skills those 5 automatically needed underneath (`document-ai-structurer`, `python-env-bootstrap`) — 7 skill folders total, packaged into one `.zip`.

## Step 2 — What's inside the .zip

Every bundle contains 4 things at the top level:

| File/folder | What it tells you |
| --- | --- |
| `skills/` | The actual skill folders — this is what you install. |
| `MANIFEST.md` | A plain-language list of everything in the bundle: what each skill does, and *why* it's included (you asked for it directly, or another skill needed it). |
| `dependency-tree.md` | The same "why is this here" information, laid out as a simple list. |
| `skills.lock` | A technical fingerprint file. You can ignore this — it exists so a later bundle can be checked against this one to confirm nothing silently changed. |

Open `MANIFEST.md` first — it's plain Markdown text, readable in any text editor, and tells you exactly what you received before you install anything.

## Step 3 — Install it into your AI assistant

Where the `skills/` folder goes depends on which assistant you use. **Only Claude Code has been directly tested and confirmed working by this project** — other harnesses (Codex CLI, Kimi CLI, etc.) follow the same open `SKILL.md` standard and should work the same way in principle, but have not been verified here; if you use one of those, treat the steps below as a starting point and confirm with that tool's own documentation.

### Claude Code (verified)

1. Unzip the bundle you received.
2. Copy the `skills/` folder's *contents* (the individual skill folders inside it, like `skills/legal-form-filler/`) into your own project's `.claude/skills/` folder, or your personal `~/.claude/skills/` folder if you want it available everywhere you use Claude Code.
3. Restart or reload Claude Code if it was already running.
4. Ask Claude Code to do the task in plain language — e.g. "check this contract for numbering consistency." It will find and use the matching skill on its own; you don't invoke a skill by name.

### Other harnesses (not yet verified — general guidance only)

Most agent harnesses that support the open `agentskills.io` `SKILL.md` standard look for skills in a folder named `skills/` somewhere in your project or a personal config directory. Check that harness's own documentation for the exact folder name and location before assuming it matches Claude Code's.

## Step 4 — Some skills need one extra setup step

A skill's own folder is self-contained instructions, but a few skills lean on a small shared toolkit (for example, `document-ai-structurer` needs a Python environment set up once via a helper skill called `python-env-bootstrap`). If your bundle's `MANIFEST.md` lists something under "Non-skill dependencies to install yourself" (for example a Python package name), that means one extra one-time setup step is needed — your AI assistant can walk you through it; you don't need to understand what the package does, just let the assistant run the setup skill once.

## Step 5 — Using it day to day

Once installed, you don't "run" a skill directly — you just describe what you want in normal language, and your assistant recognizes when a matching skill applies and uses it automatically, including its built-in checks (for example, a contract-checking skill will tell you exactly which clause number is missing or duplicated, not just "something looks off"). If a skill refuses to proceed (for example, because required information is missing), it will say exactly what's missing — that's the skill working correctly, not a malfunction; it means the check caught something a document was missing before it became a real mistake.

**A real task often needs several skills in a row, and that's expected, not wasteful.** For example, filling out a legal dossier for real might mean your assistant uses one skill to check the document is correctly structured, another to check a required clause exists, and a third to fill in the actual form — one after another, for the one task you asked for. If your assistant seems to be holding back from using multiple skills for something that genuinely needs several steps, tell it directly: this bundle's skills are meant to be chained together for one real workflow, not used sparingly one at a time.

## Getting a different/expanded bundle later

Your needs may grow — ask for an updated bundle the same way you asked the first time, describing what's changed. If you want to make sure two bundles you received at different times contain exactly the same version of a given skill, an AI assistant can compare their `skills.lock` files for you using Scriptorium's `verify_lock.py` tool — you won't need to read that file yourself.

## If something doesn't work

Tell your AI assistant what went wrong in plain language ("the contract checker isn't finding my document" / "nothing happened when I asked for X"). Every skill in this project is built to fail with a clear, specific reason rather than silently doing nothing or guessing — if you're not seeing a clear error message, that itself is worth reporting back to whoever maintains your Scriptorium setup.
