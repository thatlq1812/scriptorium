#!/usr/bin/env python3
"""Turn a flat list of study topics into a day-by-day study/review schedule.
Stdlib only (json, argparse), local, deterministic, no AI/network of any
kind — pure scheduling arithmetic. Does not teach or explain any topic
itself; it only decides WHEN to study/review WHAT, leaving the actual
studying to the student.

Algorithm (v0.1.0, intentionally simple):
    1. Each topic has a `weight` (1-5, default 2) = how many "new-study"
       sessions it needs, spread apart via round-robin interleaving so the
       same topic isn't studied twice in a row.
    2. Every Nth session in the whole schedule (--review-every, default 4)
       is a review session instead of a new one, cycling through topics
       already introduced so far.
    3. If there isn't enough session capacity (days * sessions-per-day,
       minus review slots) to fit every topic's weight, this refuses
       loudly with the minimum days needed — it never silently drops or
       compresses a topic.

Usage:
    python build_study_plan.py topics.json --days 14 --sessions-per-day 1 --output plan.md
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

MIN_WEIGHT, MAX_WEIGHT = 1, 5
MIN_REVIEW_EVERY = 2


class PlanError(Exception):
    pass


def load_topics(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlanError(f"cannot read topics file: {exc}") from exc

    topics = data.get("topics")
    if not isinstance(topics, list) or not topics:
        raise PlanError("topics.json must contain a non-empty 'topics' list")

    normalized = []
    seen_names = set()
    for i, t in enumerate(topics):
        if not isinstance(t, dict) or not t.get("name"):
            raise PlanError(f"topics[{i}] must be an object with a non-empty 'name'")
        name = str(t["name"]).strip()
        if name in seen_names:
            raise PlanError(f"duplicate topic name: {name!r}")
        seen_names.add(name)
        weight = t.get("weight", 2)
        if not isinstance(weight, int) or not (MIN_WEIGHT <= weight <= MAX_WEIGHT):
            raise PlanError(f"topics[{i}] ({name!r}) weight must be an integer {MIN_WEIGHT}-{MAX_WEIGHT}, got {weight!r}")
        normalized.append({"name": name, "weight": weight})
    return normalized


def interleave_new_sessions(topics: list[dict]) -> list[str]:
    """Round-robin the topics by remaining weight so the same topic never
    repeats back-to-back when other topics still have weight left."""
    remaining = [[t["name"], t["weight"]] for t in topics]
    ordered: list[str] = []
    while any(w > 0 for _, w in remaining):
        for entry in remaining:
            if entry[1] > 0:
                ordered.append(entry[0])
                entry[1] -= 1
    return ordered


def build_schedule(topics: list[dict], days: int, sessions_per_day: int, review_every: int) -> list[dict]:
    if days < 1:
        raise PlanError("--days must be >= 1")
    if sessions_per_day < 1:
        raise PlanError("--sessions-per-day must be >= 1")
    if review_every < MIN_REVIEW_EVERY:
        raise PlanError(f"--review-every must be >= {MIN_REVIEW_EVERY} (a value of 1 would leave zero new-study slots)")

    total_sessions = days * sessions_per_day
    review_indices = {i for i in range(1, total_sessions + 1) if i % review_every == 0}
    new_slot_count = total_sessions - len(review_indices)

    new_queue = interleave_new_sessions(topics)
    if new_slot_count < len(new_queue):
        needed_new_slots = len(new_queue)
        shortfall = needed_new_slots - new_slot_count
        extra_sessions_needed = math.ceil(shortfall * review_every / (review_every - 1))
        extra_days_needed = math.ceil(extra_sessions_needed / sessions_per_day)
        raise PlanError(
            f"not enough capacity: {len(new_queue)} new-study sessions needed (sum of topic weights) "
            f"but only {new_slot_count} non-review slots available across {days} day(s) x {sessions_per_day} "
            f"session(s)/day with review-every={review_every}. Add at least {extra_days_needed} more day(s), "
            f"increase --sessions-per-day, raise --review-every, or reduce topic weights."
        )

    schedule = []
    introduced: list[str] = []
    review_cursor = 0
    new_cursor = 0

    for session_index in range(1, total_sessions + 1):
        day = math.ceil(session_index / sessions_per_day)
        session_in_day = ((session_index - 1) % sessions_per_day) + 1

        # A slot is a review/buffer slot if it landed on a review-every
        # boundary, OR if every topic has already been introduced and
        # there's nothing left in the new-study queue (extra capacity
        # beyond what the topics needed becomes review time, not a crash).
        is_review_slot = session_index in review_indices or new_cursor >= len(new_queue)

        if is_review_slot:
            if introduced:
                topic = introduced[review_cursor % len(introduced)]
                review_cursor += 1
                entry_type = "review"
            else:
                topic = "(buffer -- no topics introduced yet)"
                entry_type = "buffer"
        else:
            topic = new_queue[new_cursor]
            new_cursor += 1
            if topic not in introduced:
                introduced.append(topic)
            entry_type = "new"

        schedule.append({"day": day, "session": session_in_day, "type": entry_type, "topic": topic})

    return schedule


def to_markdown(schedule: list[dict], topics: list[dict]) -> str:
    lines = [
        "# Study plan",
        "",
        f"Topics: {', '.join(t['name'] for t in topics)}",
        "",
        "| Day | Session | Type | Topic |",
        "| --- | --- | --- | --- |",
    ]
    for e in schedule:
        lines.append(f"| {e['day']} | {e['session']} | {e['type']} | {e['topic']} |")
    lines.append("")
    lines.append("## Checklist")
    lines.append("")
    current_day = None
    for e in schedule:
        if e["day"] != current_day:
            current_day = e["day"]
            lines.append(f"### Day {current_day}")
        lines.append(f"- [ ] ({e['type']}) {e['topic']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("topics", type=Path, help="Path to a topics JSON file (see assets/topics_template.json)")
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--sessions-per-day", type=int, default=1)
    parser.add_argument("--review-every", type=int, default=4, help="Every Nth session is a review session (default 4)")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="Print raw JSON schedule instead of Markdown")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        topics = load_topics(args.topics)
        schedule = build_schedule(topics, args.days, args.sessions_per_day, args.review_every)
    except PlanError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    output_text = json.dumps(schedule, indent=2, ensure_ascii=False) if args.json else to_markdown(schedule, topics)

    if args.output:
        if args.output.exists() and not args.force:
            print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.output.write_text(output_text, encoding="utf-8")
        print(f"OK: wrote a {len(schedule)}-session plan to {args.output}")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
