---
name: legal-corpus-ingestion
description: Deterministic ingestion, cleaning, OCR validation, structure-aware parsing, metadata extraction, and quality control for authoritative legal and regulatory PDFs used in RAG systems. Use when processing Acts, Rules, Regulations, Treaties, Protocols, Gazette notifications, or other legal source documents into citation-ready chunks for BM25, vector databases, and hybrid retrieval.
---

# Legal Corpus Ingestion Skill

## Purpose

You are a deterministic legal-document ingestion engineer.

Your task is to transform authoritative legal documents such as PDFs, scanned PDFs, Gazette notifications, Acts, Rules, Regulations, Treaties, and Protocols into clean, structured, citation-ready data for a Retrieval-Augmented Generation (RAG) system.

The output must preserve the legal meaning and hierarchy of the original source.

This skill is designed for the IP-SAKTI Sahayak project, whose corpus contains Indian intellectual-property, biodiversity, pharmaceutical, food-regulatory, and international legal sources.

---

# 1. Core Principles

## 1.1 Deterministic First

The ingestion pipeline MUST be deterministic.

Given:

- the same input file
- the same configuration
- the same parser version

the pipeline should produce the same output.

Do NOT use an LLM to:

- rewrite legal text
- summarize legal provisions
- paraphrase sections
- infer missing words
- invent metadata
- correct uncertain legal language
- merge unrelated provisions

LLMs may be used later for generation or analysis, but the corpus ingestion layer must remain deterministic wherever possible.

---

## 1.2 Never Alter Legal Meaning

Legal source text is authoritative content.

Cleaning may remove formatting noise, but MUST NOT change the meaning of the legal text.

Allowed:

- removing repeated page headers
- removing repeated footers
- removing page numbers when clearly identified
- normalizing whitespace
- joining lines broken by PDF formatting
- normalizing Unicode where semantically safe
- fixing obvious OCR spacing artifacts when confidence is high

Not allowed:

- rewriting sentences
- replacing legal terminology
- simplifying language
- changing section numbers
- changing subsection numbers
- changing dates
- changing monetary values
- changing legal references
- changing "shall" to "may"
- changing "may" to "shall"
- changing "and" to "or"
- changing negations
- silently correcting uncertain OCR

If text is uncertain, preserve the original extraction and flag it.

---

# 2. Source-of-Truth Policy

The source document is the authority.

Prefer sources in this order:

1. Official government publication
2. Official government legal database
3. Official regulatory authority
4. Official international organization
5. Official Gazette
6. Other authoritative source only if an official source is unavailable

For the IP-SAKTI corpus, prefer:

- India Code
- IP India
- CDSCO
- FSSAI
- National Biodiversity Authority / Government of India
- Official Gazette
- WTO
- Convention on Biological Diversity

Never substitute a random third-party PDF when an official source exists.

---

# 3. Input Discovery

Before processing a document:

1. Identify the input file.
2. Record filename.
3. Record file type.
4. Calculate SHA-256 checksum.
5. Determine page count.
6. Determine whether text is digitally extractable.
7. Detect whether OCR is required.
8. Record source URL if available.
9. Record acquisition date.
10. Record document title.
11. Record document version/date if identifiable.

Create a source record before modifying the document.

Example:

```json
{
  "source_id": "patents_act_1970",
  "title": "The Patents Act, 1970",
  "document_type": "Act",
  "jurisdiction": "India",
  "source_organization": "India Code",
  "source_url": "...",
  "file_name": "patents_act_1970.pdf",
  "sha256": "...",
  "page_count": 0,
  "acquired_at": "YYYY-MM-DD",
  "processing_status": "pending"
}
```

Never invent a source URL.

---

# 4. PDF Inspection

Inspect the document before extraction.

Determine:

```text
DIGITAL PDF
      OR
SCANNED PDF
      OR
HYBRID PDF
```

## Digital PDF

If text can be extracted reliably:

```text
PDF
 ↓
Text extraction
 ↓
Structure detection
 ↓
Cleaning
```

## Scanned PDF

Use OCR:

```text
PDF
 ↓
Page rendering
 ↓
OCR
 ↓
OCR validation
 ↓
Structure detection
```

## Hybrid PDF

Some pages may contain text while others are scanned.

Process pages independently where necessary.

Do NOT OCR an entire document unnecessarily if high-quality digital text already exists.

---

# 5. Text Extraction

Use deterministic extraction tools where possible.

Preferred approach:

- PyMuPDF / fitz
- pdfplumber
- OCR only when necessary

Extract text page-by-page.

Never immediately concatenate all pages into one string.

Maintain page provenance.

Example:

```json
{
  "page": 17,
  "text": "...",
  "source_id": "patents_act_1970"
}
```

Page-level provenance must survive every subsequent transformation.

---

# 6. OCR Policy

OCR is allowed only when required.

When OCR is used:

1. Preserve page number.
2. Preserve OCR output.
3. Record OCR engine/version if available.
4. Record OCR confidence when available.
5. Detect suspicious characters.
6. Detect suspicious section numbers.
7. Detect broken words.
8. Flag uncertain passages.

Common OCR problems include:

```text
Section 3(p)
→
Section 3(p)

Section 3 (p)
→
Section 3(p)
```

Potentially dangerous errors include:

```text
shall → shalI
may → rnay
1 → I
0 → O
5 → S
```

Do not silently correct ambiguous cases.

---

# 7. Cleaning Rules

Cleaning must be conservative.

## Remove

Only when clearly identified as formatting noise:

- repeated headers
- repeated footers
- page numbers
- scanning artifacts
- excessive blank lines
- repeated document titles
- obvious PDF extraction artifacts

## Preserve

Always preserve:

- section numbers
- subsection numbers
- clauses
- schedules
- articles
- chapters
- parts
- paragraphs
- provisos
- explanations
- illustrations
- exceptions
- definitions
- footnotes when legally relevant
- cross-references
- dates
- monetary amounts
- percentages
- tables where legally meaningful

---

# 8. Line Reconstruction

PDF extraction frequently creates artificial line breaks.

Example:

```text
An invention which is in effect a mere
aggregation or duplication of known
properties of traditionally known component
or components.
```

If the line breaks are purely visual, reconstruct:

```text
An invention which is in effect a mere aggregation or duplication of known properties of traditionally known component or components.
```

However, do NOT merge text when the line break represents:

- a new paragraph
- a new clause
- a new section
- a list item
- a table row
- a legal heading

---

# 9. Legal Structure Detection

This is the most important stage.

The system MUST identify legal hierarchy.

Typical hierarchy:

```text
Document
 └── Part
      └── Chapter
           └── Section / Article
                └── Subsection
                     └── Clause
                          └── Sub-clause
```

Possible patterns include:

```text
Section 3
Section 3A
Section 3(p)

3.
3A.
3(p)
3(1)
3(1)(a)

Article 5
Article 5.1

Chapter II
PART III
```

Do not assume every document uses the same numbering system.

First detect the document's structural conventions.

---

# 10. Section-Aware Chunking

NEVER use arbitrary token-window chunking as the primary legal chunking strategy.

Do NOT create:

```text
Chunk 1 = tokens 1–500
Chunk 2 = tokens 501–1000
```

Instead:

```text
Document
 ↓
Section
 ↓
Subsection
 ↓
Clause
```

Example:

```json
{
  "chunk_id": "patents_act_1970_sec_3_p",
  "source_id": "patents_act_1970",
  "section": "3(p)",
  "text": "...",
  "page_start": 12,
  "page_end": 12
}
```

---

# 11. Chunking Rules

## Rule 1

Keep a complete legal section together whenever practical.

## Rule 2

If a section is extremely long, split only at meaningful legal boundaries.

Good:

```text
Section 10
 ├── subsection (1)
 ├── subsection (2)
 └── subsection (3)
```

Bad:

```text
Section 10
 ├── arbitrary token chunk
 ├── arbitrary token chunk
 └── arbitrary token chunk
```

## Rule 3

A child clause should inherit its parent context.

For example:

```text
Section 3
Subsection (p)
```

The resulting chunk metadata should identify:

```json
{
  "section": "3",
  "subsection": "p"
}
```

If useful for retrieval, store:

```json
{
  "citation": "Section 3(p)"
}
```

---

# 12. Context Preservation

A chunk should remain understandable when retrieved independently.

For example, instead of storing only:

```text
An invention which...
```

prefer:

```text
The Patents Act, 1970

Section 3 — What are not inventions

Clause (p):

An invention which is in effect...
```

The original legal text must remain unchanged.

The contextual prefix is metadata/context, not a rewritten version of the law.

---

# 13. Metadata Schema

Every chunk MUST have structured metadata.

Minimum schema:

```json
{
  "chunk_id": "",
  "source_id": "",
  "title": "",
  "document_type": "",
  "jurisdiction": "",
  "source_organization": "",
  "source_url": "",
  "year": "",
  "version": "",
  "chapter": "",
  "part": "",
  "section": "",
  "subsection": "",
  "clause": "",
  "article": "",
  "page_start": 0,
  "page_end": 0,
  "text": "",
  "sha256": "",
  "processing_version": "",
  "ocr_used": false,
  "ocr_confidence": null,
  "quality_status": "verified"
}
```

Fields that do not apply should be `null`, not fabricated.

---

# 14. Provenance

Every chunk MUST be traceable back to the original document.

Minimum provenance:

```text
source document
page number
section/article
source URL
document version/date
file checksum
```

Example:

```json
{
  "source_id": "patents_act_1970",
  "section": "3(p)",
  "page_start": 12,
  "page_end": 12,
  "source_url": "...",
  "sha256": "..."
}
```

A retrieved chunk should always be capable of answering:

> Where did this text come from?

---

# 15. Hashing and Reproducibility

Calculate SHA-256 for:

1. Original document
2. Normalized extracted text
3. Final corpus file where practical

Example:

```text
raw PDF SHA256
      ↓
extracted text SHA256
      ↓
processed corpus SHA256
```

This allows corpus versions to be reproduced and audited.

---

# 16. Validation

Every document must pass validation before entering the production retrieval index.

## Structural validation

Check:

- sections are detected
- numbering is preserved
- headings are not accidentally removed
- page boundaries are valid
- chunk IDs are unique

## Text validation

Check:

- empty chunks
- extremely short chunks
- suspicious OCR characters
- duplicated text
- repeated pages
- missing paragraphs
- broken words

## Metadata validation

Check:

- source exists
- title exists
- jurisdiction exists
- source URL exists when known
- page numbers are valid
- section references are valid
- chunk IDs are unique

---

# 17. OCR Error Detection

Flag suspicious text when patterns appear such as:

```text
rn
cl
I0
0O
§§
@@
### 
```

Also flag:

- unusually high non-alphabetic character density
- unusually low alphabetic character density
- excessive single-character words
- broken section numbers
- impossible numbering transitions

Do NOT automatically fix uncertain cases.

Instead:

```json
{
  "quality_status": "needs_review",
  "issues": [
    "Possible OCR error near Section 3(p)"
  ]
}
```

---

# 18. Duplicate Detection

Detect:

- duplicate pages
- duplicate sections
- repeated headers
- repeated footers
- duplicate chunks

Do not automatically delete duplicate-looking legal provisions.

A provision may legitimately appear in multiple places.

Only remove duplication when it is clearly a PDF extraction artifact.

---

# 19. Tables

Legal documents may contain tables.

Never flatten a legally meaningful table blindly.

Preserve table structure where possible.

Example:

```json
{
  "content_type": "table",
  "rows": [
    ["Category", "Requirement"],
    ["A", "..."],
    ["B", "..."]
  ]
}
```

If a table cannot be extracted reliably, flag it for review.

---

# 20. Definitions

Definitions are legally important.

Preserve definition sections as independent retrievable units where appropriate.

Example:

```text
Section 2 — Definitions
```

should remain searchable independently.

Do not remove definitions merely because they appear repetitive.

---

# 21. Cross-References

Preserve legal cross-references exactly.

Example:

```text
as specified in section 8
```

must remain:

```text
as specified in section 8
```

Do not replace it with an inferred explanation.

The retrieval layer may later retrieve the referenced section.

---

# 22. Amendments

When processing amended legislation:

Do not blindly combine multiple versions.

Record:

```json
{
  "version": "...",
  "effective_date": "...",
  "source_date": "..."
}
```

If the official source provides a consolidated version, prefer the consolidated version for the primary corpus.

Historical versions may be stored separately if required.

Never silently mix historical and current provisions.

---

# 23. Gazette Notifications

Gazette documents often contain:

- notification number
- date
- ministry
- legal authority
- amendments
- schedules
- annexures

Preserve these elements when relevant.

Do not treat the entire Gazette PDF as ordinary prose.

Identify the actual regulatory text.

---

# 24. International Treaties and Protocols

For documents such as:

- TRIPS
- Convention on Biological Diversity
- Nagoya Protocol

support:

```text
Article
Paragraph
Subparagraph
Annex
```

Example:

```json
{
  "document_type": "Treaty",
  "article": "Article 27",
  "paragraph": "1"
}
```

Do not force Indian Act-style section numbering onto international instruments.

---

# 25. Output Formats

Produce at least:

```text
processed/
├── documents.json
├── chunks.jsonl
├── metadata.json
└── validation_report.json
```

Recommended chunk format:

```json
{
  "chunk_id": "patents_act_1970_sec_3_p",
  "text": "...",
  "metadata": {
    "source": "The Patents Act, 1970",
    "section": "3(p)",
    "jurisdiction": "India",
    "page_start": 12,
    "page_end": 12
  }
}
```

JSONL is preferred for large corpora because each chunk is independently readable.

---

# 26. Deterministic IDs

Generate chunk IDs deterministically.

Recommended pattern:

```text
{source_id}_{structure_identifier}
```

Examples:

```text
patents_act_1970_sec_3
patents_act_1970_sec_3_p
gi_act_1999_sec_2
trips_article_27
nagoya_article_5
```

If duplicate structures exist, add a deterministic suffix.

Never use random UUIDs unless reproducibility is not required.

---

# 27. Corpus Manifest

Maintain a manifest:

```json
{
  "corpus_version": "1.0.0",
  "created_at": "YYYY-MM-DD",
  "documents": [
    {
      "source_id": "patents_act_1970",
      "title": "The Patents Act, 1970",
      "source_url": "...",
      "sha256": "...",
      "status": "verified"
    }
  ]
}
```

The manifest is the authoritative inventory of the corpus.

---

# 28. Retrieval Readiness

Before indexing, ensure every chunk contains enough information for retrieval.

A good chunk should answer:

```text
What document?
What legal provision?
What jurisdiction?
What page?
What text?
What version?
```

Minimum:

```text
text
source
section/article
jurisdiction
page
```

---

# 29. BM25 Preparation

BM25 should index the cleaned legal text.

Before indexing:

1. Preserve legal terminology.
2. Preserve section numbers.
3. Preserve important phrases.
4. Normalize only safe whitespace/Unicode artifacts.
5. Do not remove legally meaningful stopwords blindly.

Legal words such as:

```text
shall
may
provided
unless
not
except
subject
thereof
```

can carry significant meaning.

Do not blindly apply generic NLP preprocessing that removes them.

---

# 30. Vector Preparation

For vector indexing:

```text
clean chunk
      ↓
embedding model
      ↓
vector
      ↓
Chroma
```

Store metadata alongside each vector.

Recommended metadata:

```json
{
  "source_id": "...",
  "section": "...",
  "jurisdiction": "...",
  "page_start": 0,
  "page_end": 0,
  "document_type": "Act"
}
```

---

# 31. Hybrid Retrieval Compatibility

The final corpus must support:

```text
                Query
                  │
          ┌───────┴───────┐
          ↓               ↓
        BM25            Chroma
          │               │
          ↓               ↓
      keyword          semantic
      results           results
          │               │
          └───────┬───────┘
                  ↓
            Hybrid Ranking
                  ↓
             Top Chunks
```

Every result must retain provenance.

---

# 32. Quality Gates

A document MUST NOT enter the production index if:

- extraction failed
- pages are missing
- section numbering is corrupted
- major OCR errors remain
- metadata is missing
- provenance is unavailable
- tables containing legal content are unreadable
- the source cannot be identified

Instead:

```text
status = "needs_review"
```

---

# 33. Validation Report

Generate:

```json
{
  "source_id": "patents_act_1970",
  "pages": 120,
  "chunks": 85,
  "ocr_pages": 0,
  "duplicate_chunks": 0,
  "empty_chunks": 0,
  "suspicious_chunks": 2,
  "missing_metadata": 0,
  "status": "needs_review"
}
```

The report should make failures visible.

Never hide ingestion problems.

---

# 34. Human Review

Human review is required when deterministic processing cannot confidently resolve:

- OCR ambiguity
- missing text
- unclear section boundaries
- corrupted tables
- conflicting versions
- unclear amendment status

Use:

```text
needs_review
```

rather than guessing.

---

# 35. Forbidden Behaviors

NEVER:

- hallucinate missing text
- rewrite legal provisions
- summarize during ingestion
- invent section numbers
- invent dates
- invent source URLs
- silently merge different versions
- delete suspicious text without logging
- replace official documents with random copies
- use LLM-generated text as source text
- claim OCR corrections are authoritative without validation

---

# 36. Recommended Processing Pipeline

The complete deterministic pipeline is:

```text
Official Source
      ↓
Source Registration
      ↓
SHA-256
      ↓
PDF Inspection
      ↓
Text Extraction
      ↓
OCR if Required
      ↓
Page-Level Provenance
      ↓
Conservative Cleaning
      ↓
Structure Detection
      ↓
Section / Article Parsing
      ↓
Structure-Aware Chunking
      ↓
Metadata Attachment
      ↓
Validation
      ↓
Quality Report
      ↓
Human Review if Required
      ↓
chunks.jsonl
      ↓
 ┌────┴─────┐
 ↓          ↓
BM25      Embeddings
 ↓          ↓
 │       Chroma
 └────┬─────┘
      ↓
Hybrid Retrieval
```

---

# 37. Execution Behavior

When asked to process a document:

### Phase 1 — Inspect

Report:

```text
Document:
Type:
Pages:
Digital / Scanned / Hybrid:
OCR required:
Detected structure:
```

### Phase 2 — Extract

Create page-level text with provenance.

### Phase 3 — Clean

Apply only deterministic and conservative transformations.

### Phase 4 — Structure

Identify:

- Parts
- Chapters
- Sections
- Articles
- Subsections
- Clauses
- Schedules
- Annexures

### Phase 5 — Chunk

Create legally meaningful chunks.

### Phase 6 — Validate

Run all quality checks.

### Phase 7 — Export

Produce:

```text
documents.json
chunks.jsonl
metadata.json
validation_report.json
```

### Phase 8 — Report

Summarize:

```text
Pages processed:
Chunks created:
OCR pages:
Issues found:
Needs human review:
Ready for indexing:
```

---

# 38. Example Final Chunk

```json
{
  "chunk_id": "patents_act_1970_sec_3_p",
  "text": "An invention which is in effect traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.",
  "metadata": {
    "source_id": "patents_act_1970",
    "title": "The Patents Act, 1970",
    "document_type": "Act",
    "jurisdiction": "India",
    "section": "3(p)",
    "page_start": 12,
    "page_end": 12,
    "source_organization": "India Code",
    "source_url": "...",
    "ocr_used": false,
    "quality_status": "verified"
  }
}
```

The text field must represent the source text, not an LLM-generated interpretation.

---

# 39. Success Criteria

The ingestion pipeline is successful only when:

- The source is authoritative.
- The original document is preserved.
- Extraction is reproducible.
- Legal structure is preserved.
- Sections/articles are correctly identified.
- Chunks are legally meaningful.
- Metadata is complete.
- Provenance is maintained.
- OCR errors are flagged.
- No legal meaning has been rewritten.
- BM25 can index the text.
- Chroma can index embeddings.
- Retrieval results can be traced back to the source.

The objective is not merely "clean text."

The objective is:

> **A deterministic, auditable, citation-ready legal corpus suitable for hybrid BM25 + vector retrieval.**