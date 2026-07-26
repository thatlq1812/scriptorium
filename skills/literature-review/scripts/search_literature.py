#!/usr/bin/env python3
"""Search arXiv, PubMed, and CrossRef by keyword and produce a deduplicated,
combined result list — no API key, no AI backend, stdlib only (urllib,
xml.etree). Meant as Phase 2 (systematic search) tooling for the
literature-review skill; verify individual identifiers afterward with the
`citation-management` skill.

Usage:
    python search_literature.py "crispr sickle cell" --max-results 10 \
        --sources arxiv pubmed crossref --output results.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

USER_AGENT = "Scriptorium-literature-review/0.1.0 (mailto:none-provided@example.com)"


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8")


def search_arxiv(query: str, max_results: int) -> list[dict]:
    url = (
        "http://export.arxiv.org/api/query?"
        + urllib.parse.urlencode({"search_query": f"all:{query}", "start": 0, "max_results": max_results})
    )
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(_fetch_text(url))
    results = []
    for entry in root.findall("atom:entry", ns):
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip().replace("\n", " ")
        authors = [a.findtext("atom:name", namespaces=ns) for a in entry.findall("atom:author", ns)]
        published = entry.findtext("atom:published", default="", namespaces=ns) or ""
        arxiv_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").rsplit("/", 1)[-1]
        results.append({
            "source": "arxiv", "title": title, "authors": [a for a in authors if a],
            "year": published[:4], "arxiv_id": arxiv_id, "doi": "",
        })
    return results


def search_pubmed(query: str, max_results: int) -> list[dict]:
    esearch = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
        + urllib.parse.urlencode({"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"})
    )
    ids = _fetch_json(esearch).get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    esummary = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
        + urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
    )
    data = _fetch_json(esummary).get("result", {})
    results = []
    for pmid in ids:
        record = data.get(pmid)
        if not record:
            continue
        authors = [a.get("name", "") for a in record.get("authors", [])]
        year = (record.get("pubdate") or "").split(" ")[0].split("-")[0]
        doi = next((i["value"] for i in record.get("articleids", []) if i.get("idtype") == "doi"), "")
        results.append({
            "source": "pubmed", "title": record.get("title", "").rstrip("."),
            "authors": authors, "year": year, "pmid": pmid, "doi": doi,
        })
    return results


def search_crossref(query: str, max_results: int) -> list[dict]:
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query": query, "rows": max_results})
    items = _fetch_json(url).get("message", {}).get("items", [])
    results = []
    for item in items:
        authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in item.get("author", [])]
        year = str((item.get("published") or item.get("issued") or {}).get("date-parts", [[None]])[0][0] or "")
        results.append({
            "source": "crossref", "title": " ".join(item.get("title", [])),
            "authors": authors, "year": year, "doi": item.get("DOI", ""),
        })
    return results


SEARCHERS = {"arxiv": search_arxiv, "pubmed": search_pubmed, "crossref": search_crossref}


def _dedup_key(entry: dict) -> str:
    if entry.get("doi"):
        return f"doi:{entry['doi'].lower()}"
    return "title:" + re.sub(r"[^a-z0-9]", "", entry.get("title", "").lower())


def deduplicate(entries: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for entry in entries:
        key = _dedup_key(entry)
        if key not in seen:
            seen[key] = entry
    return list(seen.values())


def to_markdown(entries: list[dict], query: str) -> str:
    lines = [f"# Search results: {query}", "", f"Total unique results: {len(entries)}", ""]
    lines.append("| Title | Authors | Year | Source | DOI |")
    lines.append("| --- | --- | --- | --- | --- |")
    for e in entries:
        authors = ", ".join(e.get("authors", [])[:3]) or "Unknown"
        lines.append(f"| {e.get('title', '')} | {authors} | {e.get('year', '')} | {e.get('source', '')} | {e.get('doi', '')} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max-results", type=int, default=10, help="Max results per source")
    parser.add_argument("--sources", nargs="+", choices=list(SEARCHERS), default=list(SEARCHERS))
    parser.add_argument("--output", type=Path, default=None, help="Write markdown table to this file")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of markdown")
    args = parser.parse_args()

    all_entries = []
    for source in args.sources:
        try:
            all_entries.extend(SEARCHERS[source](args.query, args.max_results))
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError) as exc:
            print(f"FAILED  {source}: {exc}", file=sys.stderr)

    unique = deduplicate(all_entries)

    if args.json:
        output_text = json.dumps(unique, indent=2, ensure_ascii=False)
    else:
        output_text = to_markdown(unique, args.query)

    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
        print(f"OK: wrote {len(unique)} unique results ({len(all_entries)} before dedup) to {args.output}")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
