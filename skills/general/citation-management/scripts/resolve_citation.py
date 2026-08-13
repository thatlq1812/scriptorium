#!/usr/bin/env python3
"""Resolve a DOI, PMID, or arXiv ID into a BibTeX entry using free,
no-API-key bibliographic databases (CrossRef, PubMed E-utils, arXiv Atom
API) — not an AI backend, just factual metadata lookup. Stdlib only
(urllib), network required.

Fails loudly on any identifier that does not resolve to a real record: an
identifier that is unknown, malformed, or returns an error/empty record is
reported to stderr and skipped — never emitted as a placeholder entry.

Usage:
    python resolve_citation.py 10.1038/s41586-021-03819-2   # DOI -> CrossRef
    python resolve_citation.py 33057196                      # PMID -> PubMed
    python resolve_citation.py 2401.12345                    # arXiv ID -> arXiv
    python resolve_citation.py <id1> <id2> ... --output refs.bib

Set CROSSREF_MAILTO to a real address to join CrossRef's polite pool
(optional; no fake address is ever sent).
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
PMID_RE = re.compile(r"^\d{1,9}$")
ARXIV_NEW_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
ARXIV_OLD_RE = re.compile(r"^[a-z-]+(\.[A-Za-z]{2})?/\d{7}(v\d+)?$")

DOI_URL_PREFIX_RE = re.compile(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
ARXIV_PREFIX_RE = re.compile(r"^(https?://arxiv\.org/abs/|arxiv:\s*)", re.IGNORECASE)
PMID_PREFIX_RE = re.compile(r"^(pmid:\s*)", re.IGNORECASE)

VERSION = "0.2.0"
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRY_SLEEP = 30.0

# Inline markup CrossRef/PubMed return inside titles (JATS/HTML), mapped to
# LaTeX rather than silently dropped; every other tag is stripped.
_TAG_TO_LATEX = {"i": "emph", "em": "emph", "sub": "textsubscript", "sup": "textsuperscript"}
_MARKUP_RE = re.compile(r"</?([A-Za-z][A-Za-z0-9:-]*)[^>]*>")
_OPEN, _CLOSE, _SEP = "\x00", "\x01", "\x02"

# Order matters: backslash first, then braces, then the rest.
_LATEX_ESCAPES = [
    ("\\", r"\textbackslash{}"), ("{", r"\{"), ("}", r"\}"),
    ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
    ("_", r"\_"), ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}"),
]
# Fields printed as URLs by biblatex/hyperref: only characters that break
# .bib parsing itself are escaped, the rest must stay verbatim.
_VERBATIM_FIELDS = {"doi", "eprint", "pmid", "url"}
_VERBATIM_ESCAPES = [("\\", r"\textbackslash{}"), ("{", r"\{"), ("}", r"\}"), ("%", r"\%")]


class CitationNotFound(Exception):
    """The identifier is well-formed but no real record came back."""


def _user_agent() -> str:
    mailto = os.environ.get("CROSSREF_MAILTO", "").strip()
    return f"Scriptorium-citation-management/{VERSION}" + (f" (mailto:{mailto})" if mailto else "")


def _request(url: str, accept: str, timeout: int, retries: int) -> str:
    headers = {"User-Agent": _user_agent()}
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
    try:
        return json.loads(_request(url, "application/json", timeout, retries))
    except json.JSONDecodeError as exc:
        raise CitationNotFound(f"response was not valid JSON ({exc})") from exc


def _latex_escape(value: str, field: str) -> str:
    table = _VERBATIM_ESCAPES if field in _VERBATIM_FIELDS else _LATEX_ESCAPES
    for raw, escaped in table:
        value = value.replace(raw, escaped)
    return value


def _markup_to_latex(text: str, field: str) -> str:
    """Unescape HTML entities, keep i/em/sub/sup as LaTeX, strip other tags,
    then escape LaTeX specials — in that order, so the commands we introduce
    are not themselves escaped."""
    def _mark(match: re.Match) -> str:
        tag = match.group(1).lower()
        command = _TAG_TO_LATEX.get(tag)
        if command is None:
            return ""
        return f"{_CLOSE}" if match.group(0).startswith("</") else f"{_OPEN}{command}{_SEP}"

    text = html.unescape(text)
    text = _MARKUP_RE.sub(_mark, text)
    text = _latex_escape(text, field)
    text = re.sub(rf"{_OPEN}([a-z]+){_SEP}", r"\\\1{", text).replace(_CLOSE, "}")
    return re.sub(r"\s+", " ", text).strip()


def _clean(value: object, field: str = "text") -> str:
    if value is None:
        return ""
    return _markup_to_latex(str(value), field)


def _bibtex_key(first_author_family: str, year: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]", "", first_author_family or "") or "Unknown"
    return f"{slug}{year or 'nd'}"


def _require(entry: dict, identifier: str) -> dict:
    if not entry.get("title") or entry.get("title") == "Untitled":
        raise CitationNotFound(f"no title in the record returned for {identifier}")
    return entry


def resolve_doi(doi: str, timeout: int, retries: int) -> dict:
    payload = _fetch_json(f"https://api.crossref.org/works/{urllib.request.quote(doi, safe='/')}", timeout, retries)
    data = payload.get("message")
    if not isinstance(data, dict):
        raise CitationNotFound(f"CrossRef returned no work record for {doi}")
    authors = data.get("author", []) or []
    author_str = " and ".join(
        _clean(f"{a.get('family', '')}, {a.get('given', '')}".strip(" ,")) for a in authors if a.get("family") or a.get("given")
    )
    date = data.get("issued") or data.get("published") or data.get("published-print") or data.get("published-online") or {}
    year = str((date.get("date-parts") or [[None]])[0][0] or "")
    entry_types = {"journal-article": "article", "posted-content": "misc", "book": "book",
                   "book-chapter": "incollection", "proceedings-article": "inproceedings"}
    return _require({
        "key": _bibtex_key(authors[0].get("family") if authors else "", year),
        "entrytype": entry_types.get(data.get("type", ""), "article"),
        "title": _clean(" ".join(data.get("title") or [])),
        "author": author_str,
        "journal": _clean(" ".join(data.get("container-title") or [])),
        "year": year,
        "doi": _clean(doi, "doi"),
        "volume": _clean(data.get("volume")),
        "pages": _clean(data.get("page")),
        "publisher": _clean(data.get("publisher")),
    }, doi)


def resolve_pmid(pmid: str, timeout: int, retries: int) -> dict:
    payload = _fetch_json(
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json",
        timeout, retries,
    )
    record = (payload.get("result") or {}).get(pmid)
    if not isinstance(record, dict):
        raise CitationNotFound(f"PubMed has no record for PMID {pmid}")
    if record.get("error"):
        raise CitationNotFound(f"PubMed rejected PMID {pmid}: {record['error']}")
    authors = record.get("authors", []) or []
    author_str = " and ".join(_clean(a.get("name")) for a in authors if a.get("name"))
    year = (record.get("pubdate") or "").split(" ")[0].split("-")[0]
    first_family = authors[0]["name"].split(" ")[0] if authors and authors[0].get("name") else ""
    return _require({
        "key": _bibtex_key(first_family, year),
        "entrytype": "article",
        "title": _clean((record.get("title") or "").rstrip(".")),
        "author": author_str,
        "journal": _clean(record.get("fulljournalname")),
        "year": year,
        "doi": _clean(next((i["value"] for i in record.get("articleids", []) if i.get("idtype") == "doi"), ""), "doi"),
        "pmid": _clean(pmid, "pmid"),
        "volume": _clean(record.get("volume")),
        "pages": _clean(record.get("pages")),
    }, pmid)


def resolve_arxiv(arxiv_id: str, timeout: int, retries: int) -> dict:
    xml_text = _request(
        f"http://export.arxiv.org/api/query?id_list={urllib.request.quote(arxiv_id, safe='./')}",
        "", timeout, retries,
    )
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    try:
        entry = ET.fromstring(xml_text).find("atom:entry", ns)
    except ET.ParseError as exc:
        raise CitationNotFound(f"arXiv returned unparseable XML for {arxiv_id} ({exc})") from exc
    if entry is None:
        raise CitationNotFound(f"arXiv has no entry for {arxiv_id}")
    entry_id = entry.findtext("atom:id", default="", namespaces=ns) or ""
    if "api/errors" in entry_id:
        raise CitationNotFound(f"arXiv rejected {arxiv_id}: {(entry.findtext('atom:summary', namespaces=ns) or '').strip()}")
    authors = [a.findtext("atom:name", namespaces=ns) for a in entry.findall("atom:author", ns)]
    authors = [a for a in authors if a]
    year = (entry.findtext("atom:published", default="", namespaces=ns) or "")[:4]
    published_doi = entry.findtext("arxiv:doi", default="", namespaces=ns) or ""
    return _require({
        "key": _bibtex_key(authors[0].split(" ")[-1] if authors else "", year),
        "entrytype": "misc",
        "title": _clean(entry.findtext("atom:title", default="", namespaces=ns)),
        "author": " and ".join(_clean(a) for a in authors),
        "year": year,
        "eprint": _clean(arxiv_id, "eprint"),
        "archiveprefix": "arXiv",
        "doi": _clean(published_doi, "doi"),
    }, arxiv_id)


def classify(identifier: str) -> tuple[str, str]:
    """Normalize a user-pasted identifier into (kind, bare_id)."""
    value = identifier.strip()
    if DOI_URL_PREFIX_RE.match(value):
        value = DOI_URL_PREFIX_RE.sub("", value).strip()
        if not DOI_RE.match(value):
            raise ValueError(f"'{identifier}' looks like a DOI URL but '{value}' is not a valid DOI")
        return "doi", value
    if ARXIV_PREFIX_RE.match(value):
        value = ARXIV_PREFIX_RE.sub("", value).strip()
        if not (ARXIV_NEW_RE.match(value) or ARXIV_OLD_RE.match(value)):
            raise ValueError(f"'{identifier}' looks like an arXiv reference but '{value}' is not a valid arXiv ID")
        return "arxiv", value
    if PMID_PREFIX_RE.match(value):
        value = PMID_PREFIX_RE.sub("", value).strip()
        if not PMID_RE.match(value):
            raise ValueError(f"'{identifier}' looks like a PMID reference but '{value}' is not a valid PMID")
        return "pmid", value
    if DOI_RE.match(value):
        return "doi", value
    if ARXIV_NEW_RE.match(value) or ARXIV_OLD_RE.match(value):
        return "arxiv", value
    if PMID_RE.match(value):
        return "pmid", value
    raise ValueError(f"'{identifier}' doesn't look like a DOI, PMID, or arXiv ID")


def resolve(identifier: str, timeout: int = 15, retries: int = 2) -> dict:
    kind, value = classify(identifier)
    return {"doi": resolve_doi, "pmid": resolve_pmid, "arxiv": resolve_arxiv}[kind](value, timeout, retries)


def assign_unique_keys(entries: list[dict]) -> None:
    """Suffix colliding BibTeX keys (Smith2020, Smith2020a, Smith2020b...)."""
    used: set[str] = set()
    for entry in entries:
        key = entry["key"]
        if key in used:
            for suffix in "abcdefghijklmnopqrstuvwxyz":
                if f"{key}{suffix}" not in used:
                    key = f"{key}{suffix}"
                    break
            else:
                key = f"{key}{len(used)}"
            entry["key"] = key
        used.add(key)


def to_bibtex(entry: dict) -> str:
    fields = {k: v for k, v in entry.items() if k not in ("key", "entrytype") and v}
    if "title" in fields:  # extra braces keep the original capitalization
        fields["title"] = f"{{{fields['title']}}}"
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items())
    return f"@{entry['entrytype']}{{{entry['key']},\n{body}\n}}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("identifiers", nargs="+", help="One or more DOI / PMID / arXiv ID (URL and doi:/arXiv:/PMID: prefixes accepted)")
    parser.add_argument("--output", type=Path, default=None, help="Write BibTeX to this file instead of stdout")
    parser.add_argument("--force", action="store_true", help="Overwrite --output if it already exists")
    parser.add_argument("--timeout", type=int, default=15, help="Per-request timeout in seconds (default 15)")
    parser.add_argument("--retries", type=int, default=2, help="Retries per identifier on 429/5xx and transient network errors (default 2)")
    args = parser.parse_args()

    if args.output and args.output.exists() and not args.force:
        print(f"REFUSED: {args.output} already exists, use --force to overwrite", file=sys.stderr)
        return 2

    entries: list[dict] = []
    failed: list[str] = []
    for ident in args.identifiers:
        try:
            entries.append(resolve(ident, args.timeout, args.retries))
        except (ValueError, CitationNotFound, urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, ET.ParseError, KeyError) as exc:
            failed.append(ident)
            print(f"FAILED  {ident}: {exc}", file=sys.stderr)

    assign_unique_keys(entries)
    bibtex = "\n".join(to_bibtex(e) for e in entries)

    if args.output:
        try:
            args.output.write_text(bibtex, encoding="utf-8")
        except OSError as exc:
            print(f"FAILED to write {args.output}: {exc}", file=sys.stderr)
            return 2
        print(f"OK: wrote {len(entries)} entries to {args.output}")
    elif bibtex:
        print(bibtex)

    if failed:
        print(f"{len(failed)} of {len(args.identifiers)} identifier(s) did not resolve and were NOT written: "
              f"{', '.join(failed)}", file=sys.stderr)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
