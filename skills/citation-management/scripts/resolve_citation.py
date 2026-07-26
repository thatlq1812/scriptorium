#!/usr/bin/env python3
"""Resolve a DOI, PMID, or arXiv ID into a BibTeX entry using free,
no-API-key bibliographic databases (CrossRef, PubMed E-utils, arXiv Atom
API) — not an AI backend, just factual metadata lookup. Stdlib only
(urllib), network required.

Usage:
    python resolve_citation.py 10.1038/s41586-021-03819-2   # DOI -> CrossRef
    python resolve_citation.py 33057196                      # PMID -> PubMed
    python resolve_citation.py 2401.12345                    # arXiv ID -> arXiv
    python resolve_citation.py <id1> <id2> ... --output refs.bib
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
PMID_RE = re.compile(r"^\d{4,9}$")
ARXIV_RE = re.compile(r"^(arXiv:)?(\d{4}\.\d{4,5}(v\d+)?)$", re.IGNORECASE)

USER_AGENT = "Scriptorium-citation-management/0.1.0 (mailto:none-provided@example.com)"


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def _bibtex_key(first_author_family: str, year: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]", "", first_author_family or "Unknown")
    return f"{slug}{year or 'nd'}"


def resolve_doi(doi: str) -> dict:
    data = _fetch_json(f"https://api.crossref.org/works/{doi}")["message"]
    authors = data.get("author", [])
    author_str = " and ".join(f"{a.get('family', '')}, {a.get('given', '')}" for a in authors) or "Unknown"
    year = str((data.get("published") or data.get("published-print") or data.get("published-online") or {}).get("date-parts", [[None]])[0][0] or "")
    title = " ".join(data.get("title", ["Untitled"]))
    journal = " ".join(data.get("container-title", [""]))
    key = _bibtex_key(authors[0].get("family") if authors else "Unknown", year)
    return {
        "key": key, "entrytype": "article", "title": title, "author": author_str,
        "journal": journal, "year": year, "doi": doi,
        "volume": data.get("volume", ""), "pages": data.get("page", ""),
        "publisher": data.get("publisher", ""),
    }


def resolve_pmid(pmid: str) -> dict:
    data = _fetch_json(
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
    )
    record = data["result"][pmid]
    authors = record.get("authors", [])
    author_str = " and ".join(a.get("name", "") for a in authors) or "Unknown"
    year = (record.get("pubdate") or "").split(" ")[0].split("-")[0] or ""
    first_family = authors[0]["name"].split(" ")[0] if authors else "Unknown"
    key = _bibtex_key(first_family, year)
    return {
        "key": key, "entrytype": "article", "title": record.get("title", "Untitled").rstrip("."),
        "author": author_str, "journal": record.get("fulljournalname", ""), "year": year,
        "doi": next((i["value"] for i in record.get("articleids", []) if i.get("idtype") == "doi"), ""),
        "pmid": pmid, "volume": record.get("volume", ""), "pages": record.get("pages", ""),
    }


def resolve_arxiv(arxiv_id: str) -> dict:
    xml_text = _fetch_text(f"http://export.arxiv.org/api/query?id_list={arxiv_id}")
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entry = ET.fromstring(xml_text).find("atom:entry", ns)
    title = (entry.findtext("atom:title", default="Untitled", namespaces=ns) or "").strip()
    authors = [a.findtext("atom:name", namespaces=ns) for a in entry.findall("atom:author", ns)]
    author_str = " and ".join(a for a in authors if a) or "Unknown"
    published = entry.findtext("atom:published", default="", namespaces=ns) or ""
    year = published[:4]
    first_family = authors[0].split(" ")[-1] if authors and authors[0] else "Unknown"
    key = _bibtex_key(first_family, year)
    return {
        "key": key, "entrytype": "misc", "title": title, "author": author_str, "year": year,
        "eprint": arxiv_id, "archiveprefix": "arXiv",
    }


def resolve(identifier: str) -> dict:
    identifier = identifier.strip()
    if DOI_RE.match(identifier):
        return resolve_doi(identifier)
    if ARXIV_RE.match(identifier):
        clean_id = ARXIV_RE.match(identifier).group(2)
        return resolve_arxiv(clean_id)
    if PMID_RE.match(identifier):
        return resolve_pmid(identifier)
    raise ValueError(f"'{identifier}' doesn't look like a DOI, PMID, or arXiv ID.")


def to_bibtex(entry: dict) -> str:
    fields = {k: v for k, v in entry.items() if k not in ("key", "entrytype") and v}
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items())
    return f"@{entry['entrytype']}{{{entry['key']},\n{body}\n}}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("identifiers", nargs="+", help="One or more DOI / PMID / arXiv ID")
    parser.add_argument("--output", type=Path, default=None, help="Write BibTeX to this file instead of stdout")
    args = parser.parse_args()

    entries = []
    for ident in args.identifiers:
        try:
            entries.append(resolve(ident))
        except (ValueError, urllib.error.HTTPError, urllib.error.URLError, KeyError) as exc:
            print(f"FAILED  {ident}: {exc}", file=sys.stderr)

    bibtex = "\n".join(to_bibtex(e) for e in entries)

    if args.output:
        args.output.write_text(bibtex, encoding="utf-8")
        print(f"OK: wrote {len(entries)} entries to {args.output}")
    else:
        print(bibtex)

    return 0 if len(entries) == len(args.identifiers) else 1


if __name__ == "__main__":
    raise SystemExit(main())
