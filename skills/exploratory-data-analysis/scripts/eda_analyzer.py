#!/usr/bin/env python3
"""Bounded, local-only exploratory profiling of a CSV/TSV/JSON file.

Stdlib only (csv, json, statistics). No network calls, ever. Every cell/
key/value in the input is treated as UNTRUSTED DATA: this script never
executes, imports, or follows anything found inside the file, and it never
prints raw cell values or row content — only aggregate statistics and
column/field names (structure, not data).

Path safety: the input file MUST resolve inside --root; symlinks, `..`
traversal, and files above --max-bytes are rejected. Malformed input
(undecodable bytes, oversized CSV fields, non-finite numbers, deeply nested
JSON) is refused with exit code 2 — never a traceback. This is a diagnostic
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
import math
import re
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
DEFAULT_MAX_DEPTH = 200
DEFAULT_MAX_NODES = 1_000_000
DISTINCT_CAP = 10_000
DEFAULT_MISSING_TOKENS = {"", "na", "n/a", "null", "none", "nan"}
CSV_FIELD_LIMIT = 1_000_000  # 1 MB per field; larger is refused, not silently read

# Deliberately stricter than float(): rejects "inf"/"nan" (handled separately
# as non-finite) and Python's underscore separators ("1_000" is not data).
NUMERIC_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
NON_FINITE_TOKENS = {"inf", "+inf", "-inf", "infinity", "+infinity", "-infinity", "nan", "-nan", "+nan"}


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
        raise UnsafeInputError(f"file too large ({size} bytes > cap {min(max_bytes, HARD_MAX_BYTES)})")
    return resolved


class ColumnAccumulator:
    """Streams one column into aggregates.

    Only parsed floats and a capped distinct-set are retained, never the raw
    cell strings — so memory stays bounded by --max-rows regardless of how
    wide the values are, and no raw value can leak into the report.
    """

    __slots__ = ("total", "missing", "non_finite", "non_numeric", "numeric", "distinct", "distinct_truncated")

    def __init__(self) -> None:
        self.total = 0
        self.missing = 0
        self.non_finite = 0
        self.non_numeric = 0
        self.numeric: list[float] = []
        self.distinct: set[str] = set()
        self.distinct_truncated = False

    def add(self, raw: str, missing_tokens: set[str]) -> None:
        self.total += 1
        value = raw.strip()
        if value.lower() in missing_tokens:
            self.missing += 1
            return
        if NUMERIC_RE.match(value):
            number = float(value)
            # A literal like 1e400 passes the pattern but overflows to inf on
            # parse — non-finite by value, not by token, and it must not reach
            # the statistics functions either.
            if math.isfinite(number):
                self.numeric.append(number)
            else:
                self.non_finite += 1
            return
        if value.lower() in NON_FINITE_TOKENS:
            self.non_finite += 1
            return
        self.non_numeric += 1
        if len(self.distinct) < DISTINCT_CAP:
            self.distinct.add(value)
        else:
            self.distinct_truncated = True

    def report(self) -> dict:
        present = self.total - self.missing
        stats: dict = {
            "count": self.total,
            "missing": self.missing,
            "missing_pct": round(100 * self.missing / self.total, 2) if self.total else 0.0,
            "non_finite_count": self.non_finite,
            "inferred_type": "unknown",
        }
        if present <= 0:
            stats["inferred_type"] = "all_missing"
            return stats

        stats["numeric_parse_pct"] = round(100 * len(self.numeric) / present, 2)
        if self.non_numeric == 0 and not self.numeric:
            # Every present value was non-finite (inf/nan tokens or literals
            # that overflow on parse) — neither numeric nor categorical.
            stats["inferred_type"] = "all_non_finite"
        elif self.non_numeric == 0 and self.numeric:
            stats["inferred_type"] = "numeric" if self.non_finite == 0 else "numeric_with_non_finite"
            stats.update(_numeric_stats(self.numeric))
        else:
            stats["inferred_type"] = "categorical_or_text"
            stats["distinct_count"] = len(self.distinct)
            stats["distinct_count_truncated_at_cap"] = self.distinct_truncated
            if self.numeric:
                # A mostly-numeric column with a few stray values: the reason
                # the whole column was not treated as numeric, made visible.
                stats["numeric_like_values"] = len(self.numeric)
        return stats


def _numeric_stats(nums: list[float]) -> dict:
    ordered = sorted(nums)
    n = len(ordered)
    if n >= 2:
        q1, median, q3 = statistics.quantiles(ordered, n=4, method="inclusive")
        sd = statistics.pstdev(ordered)
    else:
        q1 = median = q3 = ordered[0]
        sd = 0.0
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    outliers = sum(1 for v in ordered if v < lower_fence or v > upper_fence)
    return {
        "mean": round(statistics.fmean(ordered), 6),
        "median": round(median, 6),
        "sd": round(sd, 6),
        "min": ordered[0],
        "max": ordered[-1],
        "q1": round(q1, 6),
        "q3": round(q3, 6),
        "iqr": round(iqr, 6),
        "lower_fence": round(lower_fence, 6),
        "upper_fence": round(upper_fence, 6),
        "outlier_count_iqr_fence": outliers,
        "outlier_pct": round(100 * outliers / n, 2),
    }


def _dedup_header(header: list[str]) -> tuple[list[str], list[str]]:
    """Column names must stay 1:1 with positions — duplicates are renamed
    (`score`, `score__2`) instead of collapsing and silently dropping data."""
    names: list[str] = []
    renamed: list[str] = []
    seen: dict[str, int] = {}
    for i, raw in enumerate(header):
        name = raw.strip() or f"col_{i}"
        if name in seen:
            seen[name] += 1
            renamed.append(name)
            name = f"{name}__{seen[name]}"
        else:
            seen[name] = 1
        names.append(name)
    return names, sorted(set(renamed))


def profile_tabular(path: Path, delimiter: str, missing_tokens: set[str], max_rows: int,
                    max_cols: int, encoding: str) -> dict:
    csv.field_size_limit(CSV_FIELD_LIMIT)
    try:
        with path.open("r", encoding=encoding, newline="") as fh:
            reader = csv.reader(fh, delimiter=delimiter)
            try:
                raw_header = next(reader)
            except StopIteration:
                return {"format": "tabular", "delimiter": delimiter, "row_count": 0,
                        "column_count": 0, "columns": {}, "truncated": False, "note": "empty file"}
            columns_truncated = len(raw_header) > max_cols
            names, renamed = _dedup_header(raw_header[:max_cols])
            accumulators = [ColumnAccumulator() for _ in names]
            row_count = 0
            rows_truncated = False
            ragged_rows = 0
            for row in reader:
                if row_count >= max_rows:
                    rows_truncated = True
                    break
                if len(row) != len(raw_header):
                    ragged_rows += 1
                for i, acc in enumerate(accumulators):
                    acc.add(row[i] if i < len(row) else "", missing_tokens)
                row_count += 1
    except UnicodeDecodeError as exc:
        raise UnsafeInputError(
            f"cannot decode as {encoding} ({exc}); re-run with --encoding (e.g. latin-1, cp1252)"
        ) from exc
    except csv.Error as exc:
        raise UnsafeInputError(f"malformed CSV/TSV, refusing to guess: {exc}") from exc

    return {
        "format": "tabular",
        "delimiter": delimiter,
        "encoding": encoding,
        "row_count": row_count,
        "column_count": len(names),
        "truncated": rows_truncated,
        "columns_truncated": columns_truncated,
        "max_rows_applied": max_rows,
        "ragged_row_count": ragged_rows,
        "renamed_duplicate_headers": renamed,
        "columns": {name: acc.report() for name, acc in zip(names, accumulators)},
    }


def _walk_json(data: object, max_nodes: int, max_depth: int) -> tuple[int, int, bool]:
    """Iterative traversal — a deeply nested document must not blow the stack."""
    stack: list[tuple[object, int]] = [(data, 1)]
    nodes = 0
    deepest = 0
    while stack:
        obj, depth = stack.pop()
        if depth > max_depth:
            raise UnsafeInputError(f"JSON nesting deeper than --max-depth ({max_depth}); refusing to scan")
        nodes += 1
        deepest = max(deepest, depth)
        if nodes > max_nodes:
            return max_nodes, deepest, True
        if isinstance(obj, dict):
            stack.extend((v, depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            stack.extend((v, depth + 1) for v in obj)
    return nodes, deepest, False


def profile_json(path: Path, max_records: int, max_nodes: int, max_depth: int, encoding: str) -> dict:
    def reject_constant(name: str):
        raise UnsafeInputError(f"rejecting non-finite JSON constant: {name}")

    try:
        text = path.read_text(encoding=encoding)
    except UnicodeDecodeError as exc:
        raise UnsafeInputError(f"cannot decode as {encoding} ({exc}); re-run with --encoding") from exc
    try:
        data = json.loads(text, parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise UnsafeInputError(f"not valid JSON: {exc}") from exc
    except RecursionError as exc:
        raise UnsafeInputError(f"JSON too deeply nested for the parser: {exc}") from exc

    nodes, deepest, truncated = _walk_json(data, max_nodes, max_depth)
    report: dict = {
        "format": "json",
        "encoding": encoding,
        "top_level_type": type(data).__name__,
        "node_count_scanned": nodes,
        "max_depth_seen": deepest,
        "truncated": truncated,
    }

    if isinstance(data, list) and data and all(isinstance(x, dict) for x in data[:max_records]):
        sample = [x for x in data[:max_records] if isinstance(x, dict)]
        # Two passes: the key set must be complete before any record can be
        # judged as "missing" a key, otherwise keys that first appear late
        # are undercounted.
        key_types: dict[str, set[str]] = {}
        for record in sample:
            for key, value in record.items():
                key_types.setdefault(key, set()).add(type(value).__name__)
        key_missing = {key: 0 for key in key_types}
        key_null = {key: 0 for key in key_types}
        for record in sample:
            for key in key_types:
                if key not in record:
                    key_missing[key] += 1
                elif record[key] is None:
                    key_null[key] += 1
        report["record_count_scanned"] = len(sample)
        report["record_count_truncated"] = len(data) > len(sample)
        report["fields"] = {
            key: {
                "types_seen": sorted(types),
                "missing_count": key_missing[key],
                "missing_pct": round(100 * key_missing[key] / len(sample), 2) if sample else 0.0,
                "null_count": key_null[key],
            }
            for key, types in sorted(key_types.items())
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="Path to a .csv/.tsv/.json file")
    parser.add_argument("--root", type=Path, required=True, help="Approved root directory; input must resolve inside it")
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    parser.add_argument("--max-cols", type=int, default=DEFAULT_MAX_COLS)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH, help="JSON: refuse documents nested deeper than this")
    parser.add_argument("--max-nodes", type=int, default=DEFAULT_MAX_NODES, help="JSON: stop counting after this many nodes")
    parser.add_argument("--encoding", default="utf-8-sig", help="Text encoding (default utf-8-sig: UTF-8 with or without BOM)")
    parser.add_argument("--missing-token", action="append", default=[], help="Additional missing-value token (repeatable)")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--force", action="store_true", help="Overwrite --output if it already exists")
    args = parser.parse_args()

    if args.output and args.output.exists() and not args.force:
        print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
        return 2

    try:
        resolved = validate_input_path(args.input, args.root, args.max_bytes)
        missing_tokens = DEFAULT_MISSING_TOKENS | {t.strip().lower() for t in args.missing_token}
        suffix = resolved.suffix.lower()
        if suffix == ".json":
            report = profile_json(resolved, args.max_rows, args.max_nodes, args.max_depth, args.encoding)
        elif suffix in (".tsv", ".csv"):
            report = profile_tabular(resolved, "\t" if suffix == ".tsv" else ",",
                                     missing_tokens, args.max_rows, args.max_cols, args.encoding)
        else:
            print(f"REFUSED: unsupported format '{suffix}' — only .csv/.tsv/.json are automated in this skill",
                  file=sys.stderr)
            return 2
    except UnsafeInputError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except LookupError as exc:  # unknown --encoding name
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"REFUSED: cannot read input: {exc}", file=sys.stderr)
        return 2

    report["source_basename"] = resolved.name

    if args.output:
        try:
            args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            print(f"FAILED to write {args.output}: {exc}", file=sys.stderr)
            return 2
        print(f"OK: wrote report to {args.output}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
