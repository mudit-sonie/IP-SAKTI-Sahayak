"""Deterministic corpus ingestion: cleaned legal text -> chunks.jsonl.

Reads the cleaned per-document text produced by the preprocessing step
(``corpus/preprocessing_corpus/cleaned_corpus/documents/*.txt`` and the GI Act
markdown), detects legal structure (Chapter / Section / Article), and emits
section-aware chunks for hybrid BM25 + Chroma retrieval.

    python -m scripts.ingest_corpus            # writes backend/data/processed/
    python -m scripts.ingest_corpus --stdout   # dry run, print stats only

No LLM is used anywhere in this path. Cleaning is limited to dropping footnote /
amendment-marginalia lines and joining PDF line-wrap; legal wording is never
rewritten. See .claude/skills/legal-corpus-ingestion for the rulebook.

Outputs (backend/data/processed/):
    chunks.jsonl            one JSON object per line: {chunk_id, text, metadata}
    documents.json          per-source manifest with sha256 + chunk counts
    validation_report.json  per-source counts + flagged issues
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
CLEANED = REPO / "corpus" / "preprocessing_corpus" / "cleaned_corpus" / "documents"
GI_MD = REPO / "corpus" / "preprocessing_corpus" / "pdfs" / "The Geographical indication of Goods Act  1999.md"
OUT_DIR = BACKEND / "data" / "processed"

PROCESSING_VERSION = "ingest_corpus/1.0.0"

# --------------------------------------------------------------------------- #
# Source registry — the authoritative inventory (skill §27).
# ``parser``: "act"  -> Indian "N. Title.—body" statutes / rules
#             "gi_md" -> the GI Act markdown (## **N. Title**)
#             "articles" -> international instruments (Article N ...)
# Fields that we cannot derive deterministically from the cleaned text
# (page numbers) are left null rather than fabricated.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Source:
    source_id: str
    title: str
    filename: str
    parser: str
    jurisdiction: str
    document_type: str
    source_organization: str
    source_url: str
    year: str


SOURCES: list[Source] = [
    Source(
        "patents_act_1970", "The Patents Act, 1970",
        "THE PATENTS ACT, 1970.txt", "act", "India", "Act", "India Code",
        "https://www.indiacode.nic.in/handle/123456789/1392", "1970",
    ),
    Source(
        "trade_marks_act_1999", "The Trade Marks Act, 1999",
        "Trade Marks Act, 1999.txt", "act", "India", "Act", "India Code",
        "https://www.indiacode.nic.in/handle/123456789/1993", "1999",
    ),
    Source(
        "biological_diversity_act_2002", "The Biological Diversity Act, 2002",
        "THE BIOLOGICAL DIVERSITY ACT, 2002.txt", "act", "India", "Act", "India Code",
        "https://www.indiacode.nic.in/handle/123456789/2046", "2002",
    ),
    Source(
        "drugs_and_cosmetics_act_1940", "The Drugs and Cosmetics Act, 1940",
        "THE DRUGS AND COSMETICS ACT, 1940 (23 of 1940)1.txt", "act", "India", "Act",
        "India Code", "https://www.indiacode.nic.in/handle/123456789/2318", "1940",
    ),
    Source(
        "drugs_and_magic_remedies_act_1954",
        "The Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954",
        "Drugs and Magic Remedies (Objectionable Advertisement) Act, 1954.txt", "act",
        "India", "Act", "India Code",
        "https://www.indiacode.nic.in/handle/123456789/1391", "1954",
    ),
    Source(
        "patents_rules_2003",
        "The Patents Rules, 2003 (incorporating amendments till 15-03-2024)",
        "The Patents Rules, 2003 (incorporating all amendments till 15-03-2024).txt",
        "act", "India", "Rules", "IP India",
        "https://ipindia.gov.in/writereaddata/Portal/IPORule/1_70_1_The_Patents_Rules_2003_Updated_till_23_June_2017.pdf",
        "2003",
    ),
    Source(
        "gi_goods_act_1999",
        "The Geographical Indications of Goods (Registration and Protection) Act, 1999",
        "__gi_md__", "gi_md", "India", "Act", "India Code",
        "https://www.indiacode.nic.in/handle/123456789/1955", "1999",
    ),
    Source(
        "trips_agreement", "TRIPS Agreement (as amended by the 2005 Protocol)",
        "TRIPS Agreement — 2017 Amended Version (Official WTO).txt", "articles",
        "international", "Treaty", "WTO",
        "https://www.wto.org/english/docs_e/legal_e/31bis_trips_e.htm", "1994",
    ),
    Source(
        "cbd_1992", "Convention on Biological Diversity, 1992",
        "Convention on Biological Diversity.txt", "articles", "international", "Treaty",
        "Secretariat of the CBD", "https://www.cbd.int/convention/text/", "1992",
    ),
    Source(
        "nagoya_protocol_2010", "Nagoya Protocol on Access and Benefit-sharing, 2010",
        "CBD — Nagoya Protocol resources.txt", "articles", "international", "Protocol",
        "Secretariat of the CBD", "https://www.cbd.int/abs/text/", "2010",
    ),
]

# --------------------------------------------------------------------------- #
# Regexes
# --------------------------------------------------------------------------- #
# Section body opener, e.g. "3. What are not inventions.—The following are..."
# Tolerates a leading amendment marker like "1[8. Powers of entry..."
SEC_RE = re.compile(
    r"^\s*(?:\d+\[)?\s*(\d{1,3}[A-Z]{0,3})\.\s+([A-Za-z\[][^\n]{2,148}?)\.\s*[—–\-]{1,2}"
)
CHAP_RE = re.compile(r"^\s*(?:\d+\[)?CHAPTER\s+([IVXLCDM]+)\b(.*)$")
# Footnote / amendment marginalia: "2. Subs. by Act 38 of 2002, s. 3, ..."
FOOTNOTE_RE = re.compile(
    r"^\s*\d{1,2}\.\s*(Subs\.|Ins\.|Added|Omitted|Renumbered|Earlier|Prior|Now|"
    r"The words?|The brackets|Certain words|Clause|Sub-clause|Cl\.|Section \d|"
    r"Substituted|Inserted|This (Act|clause)|Vide|w\.e\.f)",
    re.IGNORECASE,
)
FOOTNOTE_TAIL_RE = re.compile(r"(ibid|w\.e\.f|Act \d+ of \d{4}|vide (notifn|S\.O|G\.S\.R))", re.IGNORECASE)
STAR_LINE_RE = re.compile(r"^[\s*]+$")
ARTICLE_RE = re.compile(r"^\s*Article\s+(\d{1,3})\b(.*)$")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def slugify_section(sec: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", sec.lower()).strip("_")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class DocReport:
    source_id: str
    title: str
    parser: str
    sha256: str
    chunks: int = 0
    empty_dropped: int = 0
    short_flagged: int = 0
    footnote_lines_dropped: int = 0
    issues: list[str] = field(default_factory=list)
    status: str = "verified"


# --------------------------------------------------------------------------- #
# Cleaning helpers
# --------------------------------------------------------------------------- #
def clean_body(lines: list[str]) -> tuple[str, int]:
    """Join wrapped lines, drop footnote marginalia and asterisk separators."""
    kept: list[str] = []
    dropped = 0
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if STAR_LINE_RE.match(s):
            dropped += 1
            continue
        if FOOTNOTE_RE.match(s) and (FOOTNOTE_TAIL_RE.search(s) or len(s) < 90):
            dropped += 1
            continue
        kept.append(s)
    text = " ".join(kept)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" .—", ".—")
    return text, dropped


# A top-level lettered clause opener: " (a) ", "] (c) ", "4[(b) " (amendment marker).
_CLAUSE_RE = re.compile(r"(?:^|[\s\]])(?:\d+\[)?\(([a-z]{1,2})\)\s")


def clause_split(body: str) -> tuple[str, list[tuple[str, str]]] | None:
    """Split a section that is a lettered-clause list — e.g. Patents Act s.3
    '(a) ... (b) ... (p) ...' — into (chapeau, [(letter, clause_text), ...]).

    Conservative: fires only for a genuine top-level run starting at '(a)', 4-30
    clauses, on a section long enough to be worth splitting, with no label
    repeating (a repeat means a nested list restarted). Ordinary sections and
    subsection-structured sections are left whole.
    """
    if len(body) < 800:
        return None
    marks = list(_CLAUSE_RE.finditer(body))
    start_idx = next((i for i, m in enumerate(marks) if m.group(1) == "a"), None)
    if start_idx is None:
        return None
    run = [marks[start_idx]]
    seen = {"a"}
    for m in marks[start_idx + 1:]:
        label = m.group(1)
        if label in seen:  # nested list restarted -> stop the top-level run
            break
        seen.add(label)
        run.append(m)
    if not (4 <= len(run) <= 30):
        return None
    chapeau = body[: run[0].start()].strip(" ,;:—–-")
    if len(chapeau) > 400:
        return None
    clauses: list[tuple[str, str]] = []
    for i, m in enumerate(run):
        end = run[i + 1].start() if i + 1 < len(run) else len(body)
        clauses.append((m.group(1), body[m.start():end].strip(" ,;")))
    return chapeau, clauses


def split_long(text: str, limit: int = 7000) -> list[str]:
    """Split an over-long section only at subsection ``(1) (2)`` boundaries."""
    if len(text) <= limit:
        return [text]
    parts = re.split(r"(?<=\S)\s+(?=\((?:\d{1,2}|[a-z]{1,2})\)\s)", text)
    out, buf = [], ""
    for p in parts:
        if buf and len(buf) + len(p) > limit:
            out.append(buf.strip())
            buf = p
        else:
            buf = f"{buf} {p}".strip()
    if buf:
        out.append(buf.strip())
    return out or [text]


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #
def rebreak_jammed_lines(raw: str) -> str:
    """The cleaned PDF text often jams a chapter heading, its title and the first
    section's whole body onto one physical line
    (``CHAPTER VIII 2[GRANT OF ...] 3[43. Grant of patents.—(1) Where...``).
    Put chapter headings and numbered section openers back on their own lines so
    the structural parser can see them. Conservative: only splits before a
    ``CHAPTER <roman>`` token or a ``N. Title.—`` opener (the em-dash makes false
    positives on cross-references very unlikely)."""
    raw = re.sub(r"(?<!\n)[ \t]+(CHAPTER\s+[IVXLCDM]+\b)", r"\n\1", raw)
    raw = re.sub(
        r"(?<!\n)[ \t]+((?:\d+\[)?\d{1,3}[A-Z]{0,3}\.\s+[A-Z\"“'\[][^\n]{2,140}?\.\s*[—–\-]{1,2})",
        r"\n\1",
        raw,
    )
    return raw


def find_body_start(lines: list[str]) -> int:
    for i, ln in enumerate(lines):
        if re.match(r"^\s*(?:\d+\[)?1\.\s+Short title[^\n]{0,80}?[—–\-]{1,2}", ln, re.IGNORECASE):
            return i
    for i, ln in enumerate(lines):
        if SEC_RE.match(ln):
            return i
    return 0


def parse_act(src: Source, raw: str, rep: DocReport) -> list[Chunk]:
    lines = rebreak_jammed_lines(raw).splitlines()
    start = find_body_start(lines)
    if start == 0 and not SEC_RE.match(lines[0] if lines else ""):
        rep.issues.append("could not locate section body; check source formatting")
        rep.status = "needs_review"
    chunks: list[Chunk] = []
    chapter = ""
    chapter_title = ""
    cur_sec: str | None = None
    cur_title = ""
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf, cur_sec, cur_title
        if cur_sec is None:
            buf = []
            return
        body, dropped = clean_body(buf)
        rep.footnote_lines_dropped += dropped
        buf = []
        if not body:
            rep.empty_dropped += 1
            return
        ctx = f"{src.title}"
        if chapter:
            ctx += f" — Chapter {chapter}"
            if chapter_title:
                ctx += f": {chapter_title.title()}"

        def emit(section_label: str, text: str) -> None:
            header = f"{ctx}\n\nSection {section_label} — {cur_title}\n\n"
            for k, piece in enumerate(split_long(header + text)):
                suffix = "" if k == 0 else f"_{k + 1}"
                cid = f"{src.source_id}_sec_{slugify_section(section_label)}{suffix}"
                if len(piece) < 160:
                    rep.short_flagged += 1
                chunks.append(Chunk(cid, piece, {
                    "source": src.title,
                    "source_id": src.source_id,
                    "document_type": src.document_type,
                    "jurisdiction": src.jurisdiction,
                    "source_organization": src.source_organization,
                    "source_url": src.source_url,
                    "year": src.year,
                    "chapter": chapter or None,
                    "section": section_label,
                    "citation": f"Section {section_label}",
                    "page_start": None,
                    "page_end": None,
                    "processing_version": PROCESSING_VERSION,
                    "ocr_used": False,
                    "quality_status": "needs_review" if len(piece) < 160 else "verified",
                }))

        split = clause_split(body)
        if split is not None:
            chapeau, clauses = split
            # keep the whole section as one chunk (context) ...
            emit(cur_sec, body)
            # ... plus one independently-citable chunk per clause, e.g. "3(p)"
            for letter, clause_text in clauses:
                lead = f"{chapeau}\n\n" if chapeau else ""
                emit(f"{cur_sec}({letter})", lead + clause_text)
        else:
            emit(cur_sec, body)

    i = start
    while i < len(lines):
        ln = lines[i]
        mchap = CHAP_RE.match(ln)
        if mchap and not SEC_RE.match(ln):
            flush()
            cur_sec = None
            chapter = mchap.group(1)
            tail = mchap.group(2).strip()
            title_lines = [tail] if tail else []
            j = i + 1
            while j < len(lines) and lines[j].strip() and lines[j].strip().upper() == lines[j].strip() \
                    and not SEC_RE.match(lines[j]) and not CHAP_RE.match(lines[j]) and len(title_lines) < 3:
                title_lines.append(lines[j].strip())
                j += 1
            chapter_title = " ".join(t for t in title_lines if t)
            chapter_title = re.sub(r"\d+\[|\]", "", chapter_title)  # amendment markers
            chapter_title = chapter_title[:140].strip(" [](){}*")
            i = j
            continue
        msec = SEC_RE.match(ln)
        if msec:
            flush()
            cur_sec = msec.group(1)
            cur_title = msec.group(2).strip()
            buf = [ln]
            i += 1
            continue
        if cur_sec is not None:
            buf.append(ln)
        i += 1
    flush()
    return chunks


def parse_gi_md(src: Source, raw: str, rep: DocReport) -> list[Chunk]:
    lines = raw.splitlines()
    # body starts at the enacting-formula chapter header
    chunks: list[Chunk] = []
    chapter = ""
    cur_sec: str | None = None
    cur_title = ""
    buf: list[str] = []
    sec_hdr = re.compile(r"^#{1,4}\s+\*\*\s*(\d{1,3}[A-Z]?)\.\s+(.+?)\.?\*\*\s*$")
    chap_hdr = re.compile(r"^#\s+\*\*\s*Chapter\s+([IVXLC]+)\s+(.+?)\*\*\s*$", re.IGNORECASE)

    def flush() -> None:
        nonlocal buf, cur_sec
        if cur_sec is None:
            buf = []
            return
        body, _ = clean_body(buf)
        buf = []
        if not body:
            rep.empty_dropped += 1
            return
        header = f"{src.title}"
        if chapter:
            header += f" — Chapter {chapter}"
        header += f"\n\nSection {cur_sec} — {cur_title}\n\n"
        for k, piece in enumerate(split_long(header + body)):
            suffix = "" if k == 0 else f"_{k+1}"
            chunks.append(Chunk(f"{src.source_id}_sec_{slugify_section(cur_sec)}{suffix}", piece, {
                "source": src.title, "source_id": src.source_id,
                "document_type": src.document_type, "jurisdiction": src.jurisdiction,
                "source_organization": src.source_organization, "source_url": src.source_url,
                "year": src.year, "chapter": chapter or None, "section": cur_sec,
                "citation": f"Section {cur_sec}", "page_start": None, "page_end": None,
                "processing_version": PROCESSING_VERSION, "ocr_used": False,
                "quality_status": "verified",
            }))

    seen_body = False
    for ln in lines:
        mc = chap_hdr.match(ln)
        if mc:
            flush(); cur_sec = None; chapter = mc.group(1); seen_body = True
            continue
        ms = sec_hdr.match(ln)
        if ms:
            flush(); cur_sec = ms.group(1); cur_title = ms.group(2).strip(); buf = []
            seen_body = True
            continue
        if seen_body and cur_sec is not None and not ln.startswith("#"):
            buf.append(ln)
    flush()
    if not chunks:
        rep.issues.append("gi_md parser produced no chunks")
        rep.status = "needs_review"
    return chunks


def parse_articles(src: Source, raw: str, rep: DocReport) -> list[Chunk]:
    lines = raw.splitlines()
    chunks: list[Chunk] = []
    part = ""
    cur_art: str | None = None
    cur_title = ""
    buf: list[str] = []
    part_re = re.compile(r"^\s*PART\s+([IVXLC]+)\b(.*)$")

    def flush() -> None:
        nonlocal buf, cur_art
        if cur_art is None:
            buf = []
            return
        body, _ = clean_body(buf)
        buf = []
        if not body:
            rep.empty_dropped += 1
            return
        header = f"{src.title}"
        if part:
            header += f" — Part {part}"
        header += f"\n\nArticle {cur_art}{' — ' + cur_title if cur_title else ''}\n\n"
        for k, piece in enumerate(split_long(header + body)):
            suffix = "" if k == 0 else f"_{k+1}"
            if len(piece) < 160:
                rep.short_flagged += 1
            chunks.append(Chunk(f"{src.source_id}_article_{slugify_section(cur_art)}{suffix}", piece, {
                "source": src.title, "source_id": src.source_id,
                "document_type": src.document_type, "jurisdiction": src.jurisdiction,
                "source_organization": src.source_organization, "source_url": src.source_url,
                "year": src.year, "part": part or None, "article": cur_art,
                "section": f"Article {cur_art}", "citation": f"Article {cur_art}",
                "page_start": None, "page_end": None,
                "processing_version": PROCESSING_VERSION, "ocr_used": False,
                "quality_status": "verified",
            }))

    for idx, ln in enumerate(lines):
        mp = part_re.match(ln)
        if mp and not ARTICLE_RE.match(ln):
            flush(); cur_art = None; part = mp.group(1)
            continue
        ma = ARTICLE_RE.match(ln)
        if ma:
            flush()
            cur_art = ma.group(1)
            tail = ma.group(2).strip(" .:-—–")
            cur_title = tail if tail and len(tail) < 120 else ""
            buf = []
            continue
        if cur_art is not None:
            buf.append(ln)
    flush()
    if len(chunks) < 3:
        rep.issues.append(f"articles parser produced only {len(chunks)} chunks; may need manual structuring")
        rep.status = "needs_review"
    return chunks


PARSERS = {"act": parse_act, "gi_md": parse_gi_md, "articles": parse_articles}


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def run(write: bool) -> int:
    all_chunks: list[Chunk] = []
    manifest: list[dict] = []
    reports: list[dict] = []
    seen_ids: set[str] = set()

    for src in SOURCES:
        path = GI_MD if src.parser == "gi_md" else CLEANED / src.filename
        if not path.exists():
            print(f"  !! missing: {path}", file=sys.stderr)
            reports.append({"source_id": src.source_id, "status": "missing", "issues": [str(path)]})
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rep = DocReport(src.source_id, src.title, src.parser, sha256_file(path))
        chunks = PARSERS[src.parser](src, raw, rep)

        # dedupe chunk ids deterministically
        for c in chunks:
            base = c.chunk_id
            n = 2
            while c.chunk_id in seen_ids:
                c.chunk_id = f"{base}_dup{n}"
                n += 1
            seen_ids.add(c.chunk_id)

        rep.chunks = len(chunks)
        if not chunks:
            rep.status = "needs_review"
            rep.issues.append("zero chunks produced")
        all_chunks.extend(chunks)
        manifest.append({
            "source_id": src.source_id, "title": src.title, "filename": path.name,
            "jurisdiction": src.jurisdiction, "document_type": src.document_type,
            "source_organization": src.source_organization, "source_url": src.source_url,
            "year": src.year, "sha256": rep.sha256, "chunks": len(chunks),
            "parser": src.parser, "status": rep.status,
        })
        reports.append({k: v for k, v in asdict(rep).items()})
        print(f"  {src.source_id:38s} {len(chunks):4d} chunks  "
              f"[{rep.status}]  footnote-lines dropped: {rep.footnote_lines_dropped}")

    total = len(all_chunks)
    flagged = sum(1 for c in all_chunks if c.metadata.get("quality_status") != "verified")
    india = sum(1 for c in all_chunks if c.metadata.get("jurisdiction") == "India")
    print(f"\n  TOTAL: {total} chunks  ({india} India / {total - india} international)  "
          f"{flagged} flagged needs_review")

    if not write:
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "chunks.jsonl").open("w", encoding="utf-8") as fh:
        for c in all_chunks:
            fh.write(json.dumps({"chunk_id": c.chunk_id, "text": c.text,
                                 "metadata": c.metadata}, ensure_ascii=False) + "\n")
    (OUT_DIR / "documents.json").write_text(
        json.dumps({"corpus_version": "1.0.0", "processing_version": PROCESSING_VERSION,
                    "documents": manifest}, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "validation_report.json").write_text(
        json.dumps({"total_chunks": total, "india_chunks": india,
                    "flagged_needs_review": flagged, "sources": reports},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  wrote {OUT_DIR / 'chunks.jsonl'}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stdout", action="store_true", help="dry run; print stats, write nothing")
    args = ap.parse_args()
    raise SystemExit(run(write=not args.stdout))
