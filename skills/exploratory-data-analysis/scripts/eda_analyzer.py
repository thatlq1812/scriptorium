#!/usr/bin/env python3
"""Bounded, local-only exploratory profiling of a CSV/TSV/JSON file.

Stdlib only (csv, json, statistics). No network calls, ever. Every cell/
key/value in the input is treated as UNTRUSTED DATA: this script never
executes, imports, or follows anything found inside the file, and it never
prints raw cell values or row content — only aggregate statistics and
column/field names (structure, not data).

Path safety: the input file MUST resolve inside --root; symlinks, `..`
traversal, and files above --max-bytes are rejected. This is a diagnostic
aid, not a certification of data quality — see SKILL.md for the full list
of things this script deliberately does NOT do.

Usage:
    python eda_analyzer.py data.csv --root /approved/project --output data.eda.json
    python eda_analyzer.py data.json --root /approved/project
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

DEFAULT_MAX_BYTES = 64 * 1024 * 1024  # 64 MiB
HARD_MAX_BYTES = 512 * 1024 * 1024  # 512 MiB
DEFAULT_MAX_ROWS = 100_000
DEFAULT_MAX_COLS = 2_000
DEFAULT_MISSING_TOKENS = {"", "na", "n/a", "null", "none", "nan"}


class UnsafeInputError(Exception):
    pass


def validate_input_path(path: Path, root: Path, max_bytes: int) -> Path:
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        raise UnsafeInputError(f"--root does not exist: {root} ({exc})") from exc
    if path.is_symlink():
        raise UnsafeInputError(f"refusing symlink input: {path}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise UnsafeInputError(f"input file does not exist: {path} ({exc})") from exc
    if not resolved.is_relative_to(root):
        raise UnsafeInputError(f"input must resolve inside --root ({root}), got {resolved}")
    if not resolved.is_file():
        raise UnsafeInputError(f"not a regular file: {resolved}")
    size = resolved.stat().st_size
    if size > min(max_bytes, HARD_MAX_BYTES):
        raise UnsafeInputError(f"file too large ({size} bytes > cap {max_bytes})")
    return resolved


def _is_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _column_stats(values: list[str], missing_tokens: set[str]) -> dict:
    total = len(values)
    missing = sum(1 for v in values if v.strip().lower() in missing_tokens)
    present = [v for v in values if v.strip().lower() not in missing_tokens]
    numeric_present = [v for v in present if _is_numeric(v)]
    stats: dict = {
        "count": total,
        "missing": missing,
        "missing_pct": round(100 * missing / total, 2) if total else 0.0,
        "inferred_type": "unknown",
    }
    if not present:
        stats["inferred_type"] = "all_missing"
        return stats
    if len(numeric_present) == len(present):
        nums = sorted(float(v) for v in numeric_present)
        n = len(nums)
        mean = statistics.fmean(nums)
        median = statistics.median(nums)
        sd = statistics.pstdev(nums) if n > 1 else 0.0
        q1 = nums[n // 4]
        q3 = nums[(3 * n) // 4]
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        outliers = sum(1 for v in nums if v < lower_fence or v > upper_fence)
        stats.update({
            "inferred_type": "numeric",
            "mean": round(mean, 6),
            "median": round(median, 6),
            "sd": round(sd, 6),
            "min": nums[0],
            "max": nums[-1],
            "q1": q1,
            "q3": q3,
            "iqr": round(iqr, 6),
            "outlier_count_iqr_fence": outliers,
            "outlier_pct": round(100 * outliers / n, 2) if n else 0.0,
        })
    else:
        distinct = set(present)
        stats.update({
            "inferred_type": "categorical_or_text",
            "distinct_count": len(distinct),
            "distinct_is_bounded_sample": len(distinct) >= 500,
        })
    return stats


def profile_tabular(path: Path, delimiter: str, missing_tokens: set[str],
                     max_rows: int, max_cols: int) -> dict:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration:
            return {"row_count": 0, "columns": [], "truncated": False, "note": "empty file"}
        header = header[:max_cols]
        columns: dict[str, list[str]] = {name or f"col_{i}": [] for i, name in enumerate(header)}
        names = list(columns.keys())
        row_count = 0
        truncated = False
        for row in reader:
            if row_count >= max_rows:
                truncated = True
                break
            row = row[:max_cols]
            for i, name in enumerate(names):
                columns[name].append(row[i] if i < len(row) else "")
            row_count += 1

    col_reports = {name: _column_stats(values, missing_tokens) for name, values in columns.items()}
    return {
        "format": "tabular",
        "delimiter": delimiter,
        "row_count": row_count,
        "column_count": len(names),
        "truncated": truncated,
        "max_rows_applied": max_rows,
        "columns": col_reports,
    }


def profile_json(path: Path, max_nodes: int) -> dict:
    text = path.read_text(encoding="utf-8")

    def reject_constant(name: str):
        raise UnsafeInputError(f"rejecting non-finite JSON constant: {name}")

    data = json.loads(text, parse_constant=reject_constant)

    node_count = 0

    def count_nodes(obj) -> None:
        nonlocal node_count
        if node_count > max_nodes:
            return
        node_count += 1
        if isinstance(obj, dict):
            for v in obj.values():
                count_nodes(v)
        elif isinstance(obj, list):
            for v in obj:
                count_nodes(v)

    count_nodes(data)
    truncated = node_count > max_nodes

    report: dict = {"format": "json", "top_level_type": type(data).__name__, "node_count_scanned": min(node_count, max_nodes), "truncated": truncated}

    if isinstance(data, list) and data and all(isinstance(x, dict) for x in data[:max_nodes]):
        sample = data[:max_nodes]
        key_types: dict[str, set[str]] = {}
        key_missing: dict[str, int] = {}
        for record in sample:
            keys_seen = set(record.keys())
            for key, value in record.items():
                key_types.setdefault(key, set()).add(type(value).__name__)
            for key in key_types:
                if key not in keys_seen:
                    key_missing[key] = key_missing.get(key, 0) + 1
        report["record_count_scanned"] = len(sample)
        report["fields"] = {
            key: {"types_seen": sorted(types), "missing_count": key_missing.get(key, 0)}
            for key, types in key_types.items()
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="Path to a .csv/.tsv/.json file")
    parser.add_argument("--root", type=Path, required=True, help="Approved root directory; input must resolve inside it")
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    parser.add_argument("--max-cols", type=int, default=DEFAULT_MAX_COLS)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--missing-token", action="append", default=[], help="Additional missing-value token (repeatable)")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--force", action="store_true", help="Overwrite --output if it already exists")
    args = parser.parse_args()

    try:
        resolved = validate_input_path(args.input, args.root, args.max_bytes)
    except UnsafeInputError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    missing_tokens = DEFAULT_MISSING_TOKENS | {t.strip().lower() for t in args.missing_token}
    suffix = resolved.suffix.lower()

    if suffix == ".json":
        report = profile_json(resolved, max_nodes=args.max_rows * max(args.max_cols, 1))
    elif suffix == ".tsv":
        report = profile_tabular(resolved, "\t", missing_tokens, args.max_rows, args.max_cols)
    elif suffix == ".csv":
        report = profile_tabular(resolved, ",", missing_tokens, args.max_rows, args.max_cols)
    else:
        print(f"REFUSED: unsupported format '{suffix}' — only .csv/.tsv/.json are automated in this skill", file=sys.stderr)
        return 2

    report["source_basename"] = resolved.name

    if args.output:
        if args.output.exists() and not args.force:
            print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"OK: wrote report to {args.output}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UnsafeInputError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
