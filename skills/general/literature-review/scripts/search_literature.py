#!/usr/bin/env python3
"""Search arXiv, PubMed, and CrossRef by keyword and produce a deduplicated,
combined result list with the record counts a PRISMA-style screening flow
needs — no API key, no AI backend, stdlib only (urllib, xml.etree).

Deduplication is cross-source: a record is merged with an existing one when
either its DOI or its normalized title matches, so an arXiv preprint and its
published CrossRef/PubMed record collapse into a single row listing both
sources. Verify individual identifiers afterward with `citation-management`.

Usage:
    python search_literature.py "crispr sickle cell" --max-results 10 \
        --sources arxiv pubmed crossref --from-year 2015 --abstracts \
        --output results.md

Exit codes: 0 = every requested source answered, 1 = some sources failed
(partial results), 2 = every source failed / refused to overwrite output.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VERSION = "0.2.0"
USER_AGENT = f"Scriptorium-literature-review/{VERSION}"
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRY_SLEEP = 30.0
DEFAULT_ABSTRACT_CHARS = 1500

_TAG_RE = re.compile(r"<[^>]+>")


def _request(url: str, accept: str, timeout: int, retries: int) -> str:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in RETRY_STATUSES or attempt == retries:
                raise
            delay = min(float(exc.headers.get("Retry-After") or 0) or 2.0 ** attempt, MAX_RETRY_SLEEP)
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == retries:
                raise
            delay = 2.0 ** attempt
        time.sleep(delay)
    raise last_error if last_error else RuntimeError("unreachable")


def _fetch_json(url: str, timeout: int, retries: int) -> dict:
    return json.loads(_request(url, "application/json", timeout, retries))


def _plain(text: str | None) -> str:
    """Strip markup, unescape entities, collapse whitespace to one line."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", html.unescape(_TAG_RE.sub(" ", text))).strip()


def search_arxiv(query: str, max_results: int, timeout: int, retries: int, abstracts: bool) -> list[dict]:
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": f"all:{query}", "start": 0, "max_results": max_results}
    )
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(_request(url, "", timeout, retries))
    results = []
    for entry in root.findall("atom:entry", ns):
        authors = [a.findtext("atom:name", namespaces=ns) for a in entry.findall("atom:author", ns)]
        published = entry.findtext("atom:published", default="", namespaces=ns) or ""
        arxiv_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").rsplit("/", 1)[-1]
        results.append({
            "source": "arxiv",
            "title": _plain(entry.findtext("atom:title", namespaces=ns)),
            "authors": [_plain(a) for a in authors if a],
            "year": published[:4],
            "arxiv_id": arxiv_id,
            # arXiv publishes the journal DOI once an entry is published — the
            # key that lets a preprint merge with its CrossRef/PubMed record.
            "doi": _plain(entry.findtext("arxiv:doi", namespaces=ns)),
            "abstract": _plain(entry.findtext("atom:summary", namespaces=ns)) if abstracts else "",
        })
    return results


def _pubmed_abstracts(pmids: list[str], timeout: int, retries: int) -> dict[str, str]:
    if not pmids:
        return {}
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "rettype": "abstract"}
    )
    try:
        root = ET.fromstring(_request(url, "", timeout, retries))
    except (ET.ParseError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        print(f"WARN  pubmed abstracts unavailable: {exc}", file=sys.stderr)
        return {}
    out: dict[str, str] = {}
    for article in root.iter("PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID", default="")
        parts = ["".join(node.itertext()) for node in article.iter("AbstractText")]
        if pmid and parts:
            out[pmid] = _plain(" ".join(parts))
    return out


def search_pubmed(query: str, max_results: int, timeout: int, retries: int, abstracts: bool) -> list[dict]:
    esearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
    )
    ids = _fetch_json(esearch, timeout, retries).get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    esummary = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
    )
    data = _fetch_json(esummary, timeout, retries).get("result", {})
    abstract_map = _pubmed_abstracts(ids, timeout, retries) if abstracts else {}
    results = []
    for pmid in ids:
        record = data.get(pmid)
        if not isinstance(record, dict) or record.get("error"):
            continue
        results.append({
            "source": "pubmed",
            "title": _plain((record.get("title") or "").rstrip(".")),
            "authors": [_plain(a.get("name")) for a in record.get("authors", []) if a.get("name")],
            "year": (record.get("pubdate") or "").split(" ")[0].split("-")[0],
            "pmid": pmid,
            "doi": next((i["value"] for i in record.get("articleids", []) if i.get("idtype") == "doi"), ""),
            "abstract": abstract_map.get(pmid, ""),
        })
    return results


def search_crossref(query: str, max_results: int, timeout: int, retries: int, abstracts: bool) -> list[dict]:
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query": query, "rows": max_results})
    items = _fetch_json(url, timeout, retries).get("message", {}).get("items", [])
    results = []
    for item in items:
        authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in item.get("author", [])]
        date = item.get("issued") or item.get("published") or {}
        results.append({
            "source": "crossref",
            "title": _plain(" ".join(item.get("title") or [])),
            "authors": [_plain(a) for a in authors if a],
            "year": str((date.get("date-parts") or [[None]])[0][0] or ""),
            "doi": item.get("DOI", ""),
            "abstract": _plain(item.get("abstract")) if abstracts else "",
        })
    return results


SEARCHERS = {"arxiv": search_arxiv, "pubmed": search_pubmed, "crossref": search_crossref}


def _title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())


def deduplicate(entries: list[dict]) -> list[dict]:
    """Merge records that share a DOI or a normalized title, across sources.

    Both keys point at the same merged record, so an arXiv entry (DOI-less at
    preprint time, or carrying the published DOI) still collapses into the
    CrossRef/PubMed record of the same paper.
    """
    by_doi: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    merged: list[dict] = []

    for entry in entries:
        doi = (entry.get("doi") or "").lower().strip()
        tkey = _title_key(entry.get("title", ""))
        target = by_doi.get(doi) if doi else None
        if target is None and tkey:
            target = by_title.get(tkey)

        if target is None:
            record = dict(entry)
            record["sources"] = [entry.get("source", "")]
            record.pop("source", None)
            merged.append(record)
            target = record
        else:
            if entry.get("source") and entry["source"] not in target["sources"]:
                target["sources"].append(entry["source"])
            for field in ("doi", "pmid", "arxiv_id", "year", "abstract", "title"):
                if not target.get(field) and entry.get(field):
                    target[field] = entry[field]
            if len(entry.get("authors", [])) > len(target.get("authors", [])):
                target["authors"] = entry["authors"]

        if doi:
            by_doi[doi] = target
        if tkey:
            by_title[tkey] = target
    return merged


def filter_by_year(entries: list[dict], from_year: int | None, to_year: int | None) -> tuple[list[dict], int, int]:
    """Returns (kept, excluded_out_of_range, excluded_unknown_year)."""
    if from_year is None and to_year is None:
        return entries, 0, 0
    kept, out_of_range, unknown = [], 0, 0
    for entry in entries:
        raw = (entry.get("year") or "").strip()
        if not raw.isdigit():
            unknown += 1
            continue
        year = int(raw)
        if (from_year is not None and year < from_year) or (to_year is not None and year > to_year):
            out_of_range += 1
            continue
        kept.append(entry)
    return kept, out_of_range, unknown


def _cell(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).replace("|", r"\|").strip()


def to_markdown(entries: list[dict], query: str, counts: dict, abstract_chars: int) -> str:
    lines = [
        f"# Search results: {query}", "",
        "## Screening counts (for the review template's PRISMA flow)", "",
        "| Stage | n |", "| --- | --- |",
    ]
    for source, raw in counts["per_source"].items():
        lines.append(f"| Raw hits — {source} | {raw} |")
    lines += [
        f"| Combined before dedup | {counts['combined']} |",
        f"| After deduplication | {counts['after_dedup']} |",
    ]
    if counts["year_filter"]:
        lines += [
            f"| Excluded by year filter {counts['year_filter']} | {counts['excluded_year']} |",
            f"| Excluded — no usable year | {counts['excluded_unknown_year']} |",
            f"| After year filter | {len(entries)} |",
        ]
    if counts["failed_sources"]:
        lines.append(f"| Sources that FAILED (results incomplete) | {', '.join(counts['failed_sources'])} |")

    lines += ["", "## Results", "", "| # | Title | Authors | Year | Sources | DOI |", "| --- | --- | --- | --- | --- | --- |"]
    for i, e in enumerate(entries, start=1):
        authors = ", ".join(e.get("authors", [])[:3]) or "Unknown"
        if len(e.get("authors", [])) > 3:
            authors += " et al."
        lines.append(
            f"| {i} | {_cell(e.get('title'))} | {_cell(authors)} | {_cell(e.get('year'))} | "
            f"{_cell(', '.join(e.get('sources', [])))} | {_cell(e.get('doi'))} |"
        )

    if any(e.get("abstract") for e in entries):
        lines += ["", "## Abstracts (for title/abstract screening)", ""]
        for i, e in enumerate(entries, start=1):
            abstract = e.get("abstract") or "(no abstract returned by the source)"
            if len(abstract) > abstract_chars:
                abstract = abstract[:abstract_chars].rstrip() + "..."
            lines += [f"### {i}. {_cell(e.get('title'))}", "", abstract, ""]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max-results", type=int, default=10, help="Max results per source")
    parser.add_argument("--sources", nargs="+", choices=list(SEARCHERS), default=list(SEARCHERS))
    parser.add_argument("--from-year", type=int, default=None, help="Drop records published before this year")
    parser.add_argument("--to-year", type=int, default=None, help="Drop records published after this year")
    parser.add_argument("--abstracts", action="store_true", help="Also fetch abstracts (needed for abstract screening)")
    parser.add_argument("--abstract-chars", type=int, default=DEFAULT_ABSTRACT_CHARS, help="Truncate each abstract to this length")
    parser.add_argument("--output", type=Path, default=None, help="Write markdown to this file")
    parser.add_argument("--force", action="store_true", help="Overwrite --output if it already exists")
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout in seconds")
    parser.add_argument("--retries", type=int, default=2, help="Retries per source on 429/5xx and transient network errors")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of markdown")
    args = parser.parse_args()

    if args.from_year is not None and args.to_year is not None and args.from_year > args.to_year:
        print("REFUSED: --from-year is later than --to-year", file=sys.stderr)
        return 2
    if args.output and args.output.exists() and not args.force:
        print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
        return 2

    all_entries: list[dict] = []
    per_source: dict[str, int] = {}
    failed_sources: list[str] = []
    for source in args.sources:
        try:
            found = SEARCHERS[source](args.query, args.max_results, args.timeout, args.retries, args.abstracts)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ET.ParseError,
                json.JSONDecodeError, KeyError) as exc:
            failed_sources.append(source)
            per_source[source] = 0
            print(f"FAILED  {source}: {exc}", file=sys.stderr)
            continue
        per_source[source] = len(found)
        all_entries.extend(found)

    if failed_sources and len(failed_sources) == len(args.sources):
        print("FAILED: every requested source failed — no results to report.", file=sys.stderr)
        return 2

    unique = deduplicate(all_entries)
    after_dedup = len(unique)
    unique, excluded_year, excluded_unknown = filter_by_year(unique, args.from_year, args.to_year)

    year_filter = ""
    if args.from_year is not None or args.to_year is not None:
        year_filter = f"{args.from_year or 'any'}-{args.to_year or 'any'}"
    counts = {
        "per_source": per_source, "combined": len(all_entries), "after_dedup": after_dedup,
        "year_filter": year_filter, "excluded_year": excluded_year,
        "excluded_unknown_year": excluded_unknown, "failed_sources": failed_sources,
    }

    if args.json:
        output_text = json.dumps({"query": args.query, "counts": counts, "results": unique}, indent=2, ensure_ascii=False)
    else:
        output_text = to_markdown(unique, args.query, counts, args.abstract_chars)

    if args.output:
        try:
            args.output.write_text(output_text, encoding="utf-8")
        except OSError as exc:
            print(f"FAILED to write {args.output}: {exc}", file=sys.stderr)
            return 2
        print(f"OK: wrote {len(unique)} records to {args.output} "
              f"({len(all_entries)} raw, {after_dedup} after dedup)")
    else:
        print(output_text)

    if failed_sources:
        print(f"PARTIAL: {', '.join(failed_sources)} failed — the counts above are incomplete, "
              f"do not report them as a full search.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
