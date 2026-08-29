# ⚖️ Legal Corpus Ingestion

> Deterministic PDF ingestion and processing skill for building a citation-ready legal corpus for **IP-SAKTI Sahayak**.

This skill is responsible for converting authoritative legal documents into **clean, structured, traceable, and retrieval-ready data**.

It is designed specifically for legal PDFs such as:

- Acts
- Rules
- Regulations
- Treaties
- Protocols
- Gazette notifications
- Government publications
- Regulatory documents

The skill prioritizes **deterministic processing and preservation of legal meaning** over AI-generated transformation.

---

## 🎯 Objective

The ingestion pipeline transforms:

```text
Official Legal Sources
        │
        ▼
Document Collection
        │
        ▼
PDF / Text Extraction
        │
        ▼
OCR (when required)
        │
        ▼
Conservative Cleaning
        │
        ▼
Structure-Aware Parsing
        │
        ▼
Section / Clause Chunking
        │
        ▼
Metadata Extraction
        │
        ▼
Validation
        │
        ▼
Citation-Ready Corpus
```

The resulting corpus can then be consumed by downstream retrieval systems such as:

```text
BM25 + Vector Embeddings
          │
          ▼
       Chroma
          │
          ▼
   Hybrid Retrieval
```

---

# 🧠 Why Deterministic Ingestion?

Legal documents cannot be treated like ordinary text.

An LLM might:

```text
"shall" → "may"
```

or accidentally:

```text
Section 3(p) → Section 3
```

Even a small modification can change the legal meaning.

Therefore, this skill follows a strict principle:

> **The ingestion layer must preserve the source. It must not interpret the source.**

The LLM should not rewrite, summarize, or paraphrase legal provisions during ingestion.

---

# 🔄 Processing Pipeline

```text
                    PDF
                     │
                     ▼
              PDF Inspection
                     │
          ┌──────────┴──────────┐
          │                     │
       Digital                Scanned
          │                     │
          ▼                     ▼
    Text Extraction            OCR
          │                     │
          └──────────┬──────────┘
                     ▼
             Page Provenance
                     │
                     ▼
          Conservative Cleaning
                     │
                     ▼
         Structure-Aware Parsing
                     │
                     ▼
          Section / Clause Data
                     │
                     ▼
            Metadata Extraction
                     │
                     ▼
               Validation
                     │
                     ▼
             JSON / JSONL
```

---

# 📂 What This Skill Handles

## 1. PDF Inspection

The skill determines whether a document is:

```text
Digital PDF
Scanned PDF
Hybrid PDF
```

It avoids unnecessary OCR when a reliable text layer already exists.

---

## 2. Text Extraction

Digital PDFs are processed using deterministic extraction tools.

Typical tools include:

- PyMuPDF
- pdfplumber

Text is extracted **page-by-page**.

Example:

```json
{
  "page": 12,
  "text": "...",
  "source_id": "patents_act_1970"
}
```

Page information is never discarded because it is required for citation provenance.

---

## 3. OCR

Scanned documents are processed using OCR only when required.

The pipeline should detect potential OCR problems such as:

```text
shall → shalI
may → rnay
Section → Sectlon
```

Uncertain OCR must be **flagged rather than silently corrected**.

---

# 🧹 Conservative Cleaning

Cleaning removes formatting noise while preserving legal meaning.

### Safe transformations

- Remove repeated headers
- Remove repeated footers
- Remove obvious page numbers
- Normalize excessive whitespace
- Repair visual line wrapping
- Normalize safe Unicode artifacts

### Never modify

- Section numbers
- Clause numbers
- Dates
- Legal terminology
- Monetary values
- Percentages
- Negations
- Cross-references
- Definitions
- Exceptions
- Provisos

For example:

```text
shall
```

must never be automatically changed to:

```text
may
```

---

# ⚖️ Structure-Aware Processing

Legal documents have a hierarchy.

For example:

```text
PART
 └── CHAPTER
      └── SECTION
           └── SUBSECTION
                └── CLAUSE
```

International documents may instead use:

```text
ARTICLE
 └── PARAGRAPH
      └── SUBPARAGRAPH
```

The ingestion process preserves the structure used by the original document.

It does not force every document into the same structure.

---

# ✂️ Section-Aware Chunking

The skill is designed for **legal structure-aware chunking**.

### ❌ Avoid

```text
500 tokens
     ↓
500 tokens
     ↓
500 tokens
```

### ✅ Prefer

```text
Section 3
    │
    ├── (a)
    ├── (b)
    ├── (c)
    └── (p)
```

For example:

```json
{
  "chunk_id": "patents_act_1970_sec_3_p",
  "section": "3",
  "clause": "p",
  "page_start": 12,
  "page_end": 12,
  "text": "..."
}
```

This allows downstream retrieval to return a specific legal provision rather than an arbitrary portion of a page.

---

# 🧾 Metadata

Each document and chunk should contain structured metadata.

Example:

```json
{
  "title": "The Patents Act, 1970",
  "document_type": "Act",
  "jurisdiction": "India",
  "year": 1970,
  "section": "Section 3(p)",
  "source_organization": "India Code",
  "source_url": "https://www.indiacode.nic.in/",
  "version": null,
  "effective_date": null
}
```

Additional provenance can include:

```json
{
  "page_start": 12,
  "page_end": 12,
  "ocr_used": false,
  "sha256": "..."
}
```

Unavailable information should be represented as `null`.

The skill must never invent metadata.

---

# 🔗 Provenance

Every piece of processed text must remain traceable to the original source.

At minimum:

```text
Document
Section / Article
Page
Source Organization
Source URL
Version
SHA-256
```

The system should always be able to answer:

> **Where did this piece of text come from?**

---

# 🧪 Validation

Before a document enters the retrieval index, it should be validated.

### Structural checks

- Missing sections
- Broken numbering
- Incorrect hierarchy
- Duplicate chunks
- Missing pages

### Text checks

- Empty chunks
- OCR anomalies
- Broken words
- Suspicious characters
- Excessive whitespace

### Metadata checks

- Missing document title
- Missing source
- Missing jurisdiction
- Missing section/article
- Invalid page numbers
- Missing provenance

Example validation result:

```json
{
  "document": "patents_act_1970",
  "pages": 120,
  "chunks": 85,
  "ocr_pages": 3,
  "duplicate_chunks": 0,
  "empty_chunks": 0,
  "suspicious_chunks": 2,
  "status": "needs_review"
}
```

---

# 📦 Expected Output

The skill should produce structured files such as:

```text
processed/
├── documents.json
├── chunks.jsonl
├── metadata.json
└── validation_report.json
```

### `documents.json`

Contains document-level information.

### `chunks.jsonl`

Contains one retrieval-ready legal chunk per line.

### `metadata.json`

Contains metadata and provenance.

### `validation_report.json`

Contains quality-control results.

---

# 🗂️ Recommended Directory Structure

```text
corpus/
│
├── raw/
│   ├── india/
│   └── international/
│
├── extracted/
│
├── cleaned/
│
├── structured/
│
├── processed/
│   ├── documents.json
│   ├── chunks.jsonl
│   ├── metadata.json
│   └── validation_report.json
│
└── corpus_manifest.json
```

---

# 🔐 Source Integrity

The original PDFs should remain untouched.

Recommended flow:

```text
raw/
  │
  │  NEVER MODIFY
  ▼
extracted/
  │
  ▼
cleaned/
  │
  ▼
structured/
  │
  ▼
processed/
```

The `raw/` directory acts as the immutable source layer.

---

# 🧮 Reproducibility

The pipeline should use SHA-256 hashes to identify source files.

Example:

```text
patents_act_1970.pdf
        │
        ▼
     SHA-256
        │
        ▼
  corpus_manifest.json
```

This makes it possible to determine exactly which source document produced a particular corpus version.

---

# 🚨 Human Review

The system must not guess when deterministic processing is uncertain.

Cases requiring review include:

- Uncertain OCR
- Missing pages
- Broken section boundaries
- Unreadable tables
- Conflicting versions
- Unknown document metadata

Use:

```text
needs_review
```

instead of silently making a correction.

---

# 🚫 What This Skill Must Never Do

The ingestion skill must **never**:

- Hallucinate legal text
- Rewrite legal provisions
- Summarize legal provisions
- Paraphrase source text
- Invent section numbers
- Invent dates
- Invent source URLs
- Silently modify legal terminology
- Mix different legislation versions
- Remove legally meaningful content
- Use generated text as authoritative source text

---

# ✅ Definition of Done

A document is ready for indexing when:

- [ ] Official source identified
- [ ] Original PDF preserved
- [ ] SHA-256 recorded
- [ ] PDF type detected
- [ ] Text extracted
- [ ] OCR performed when necessary
- [ ] OCR anomalies checked
- [ ] Formatting noise removed
- [ ] Legal hierarchy preserved
- [ ] Sections/articles detected
- [ ] Legal chunks generated
- [ ] Metadata attached
- [ ] Page provenance preserved
- [ ] Validation completed
- [ ] Review issues resolved or flagged
- [ ] Output generated successfully

---

# 🎯 Design Philosophy

This skill is not designed to make an LLM "understand" a PDF.

It is designed to build a **reliable evidence layer** that AI systems can safely retrieve from.

```text
Authoritative Source
        ↓
Deterministic Ingestion
        ↓
Structured Legal Evidence
        ↓
Traceable Metadata
        ↓
Hybrid Retrieval
        ↓
Grounded AI
```

> **Better evidence → better retrieval → better answers.**

The ingestion layer should be boring, deterministic, reproducible, and auditable.

That is exactly what makes the system reliable.
