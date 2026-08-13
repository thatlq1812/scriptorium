#!/usr/bin/env python3
"""Structured GitHub repo lookup for scouting harvest candidates — wraps the
`gh` CLI (already authenticated in this environment) instead of hand-typing
`gh api`/`gh search` each time. Stdlib only, requires `gh` on PATH.

Repo inspection (stars, license, description, topics):
    python github_scout.py repo google-gemini/gemini-cli

Search (ranked by stars):
    python github_scout.py search "agent skills claude" --limit 10

Both print a structured table AND write JSON to stdout with --json for
piping into another step.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def require_gh() -> None:
    if shutil.which("gh") is None:
        sys.exit("gh CLI not found on PATH. Install: https://cli.github.com/")


def run_gh(args: list[str]) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def inspect_repo(slug: str) -> dict:
    raw = run_gh([
        "api", f"repos/{slug}",
        "--jq", "{full_name, stars: .stargazers_count, license: .license.spdx_id, "
        "description, topics, archived, pushed_at, homepage}",
    ])
    return json.loads(raw)


def search_repos(query: str, limit: int) -> list[dict]:
    raw = run_gh([
        "search", "repos", query,
        "--limit", str(limit),
        "--sort", "stars",
        "--json", "fullName,stargazersCount,license,description,updatedAt",
    ])
    results = json.loads(raw)
    return [
        {
            "full_name": r["fullName"],
            "stars": r["stargazersCount"],
            "license": (r.get("license") or {}).get("key"),
            "description": r.get("description"),
            "updated_at": r.get("updatedAt"),
        }
        for r in results
    ]


def print_table(rows: list[dict]) -> None:
    if not rows:
        print("No results.")
        return
    keys = list(rows[0].keys())
    widths = {k: max(len(k), *(len(str(r.get(k, ""))) for r in rows)) for k in keys}
    header = "  ".join(k.ljust(widths[k]) for k in keys)
    print(header)
    print("-" * len(header))
    for r in rows:
        print("  ".join(str(r.get(k, "")).ljust(widths[k]) for k in keys))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    repo_cmd = sub.add_parser("repo", help="Inspect a single repo")
    repo_cmd.add_argument("slug", help="owner/repo")
    repo_cmd.add_argument("--json", action="store_true", help="Print raw JSON instead of a table")

    search_cmd = sub.add_parser("search", help="Search repos, ranked by stars")
    search_cmd.add_argument("query")
    search_cmd.add_argument("--limit", type=int, default=10)
    search_cmd.add_argument("--json", action="store_true", help="Print raw JSON instead of a table")

    args = parser.parse_args()
    require_gh()

    try:
        if args.command == "repo":
            data = inspect_repo(args.slug)
            rows = [data]
        else:
            rows = search_repos(args.query, args.limit)
    except RuntimeError as exc:
        sys.exit(str(exc))

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(rows)

    print(
        "\nReminder: this is scouting only, not a license decision. "
        "Every candidate still needs license-compliance-check before touching skill-creator.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
