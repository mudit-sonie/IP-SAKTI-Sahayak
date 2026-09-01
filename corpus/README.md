# 📚 Data Sources

The **IP-SAKTI Sahayak** knowledge base is built using authoritative legal and regulatory sources from official government and international organizations. These sources form the corpus used for document retrieval, citation, and RAG-based question answering.

---

## 📑 Corpus Sources

| # | Data Source | Type | Jurisdiction | Official Source |
|---:|---|---|---|---|
| 1 | **The Patents Act, 1970** | Central Act | 🇮🇳 India | [India Code](https://www.indiacode.nic.in/) |
| 2 | **The Patents Rules, 2003 — incorporating amendments till 15-03-2024** | Rules | 🇮🇳 India | [IP India](https://www.ipindia.gov.in/) |
| 3 | **The Biological Diversity Act, 2002** | Central Act | 🇮🇳 India | [India Code](https://www.indiacode.nic.in/) |
| 4 | **The Biological Diversity Rules, 2024** | Rules | 🇮🇳 India | [India Code](https://www.indiacode.nic.in/) |
| 5 | **The Drugs and Cosmetics Act, 1940** | Central Act | 🇮🇳 India | [India Code](https://www.indiacode.nic.in/) |
| 6 | **The Drugs and Cosmetics Rules, 1945** | Rules | 🇮🇳 India | [CDSCO](https://www.cdsco.gov.in/) |
| 7 | **The Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954** | Central Act | 🇮🇳 India | [India Code](https://www.indiacode.nic.in/) |
| 8 | **Food Safety and Standards (Ayurveda Aahara) Regulations, 2022** | Regulations | 🇮🇳 India | [FSSAI](https://www.fssai.gov.in/) |
| 9 | **The Geographical Indications of Goods (Registration and Protection) Act, 1999** | Central Act | 🇮🇳 India | [India Code](https://www.indiacode.nic.in/) |
| 10 | **The Trade Marks Act, 1999** | Central Act | 🇮🇳 India | [India Code](https://www.indiacode.nic.in/) |
| 11 | **Agreement on Trade-Related Aspects of Intellectual Property Rights (TRIPS)** | International Agreement | 🌍 International | [WTO](https://www.wto.org/) |
| 12 | **Convention on Biological Diversity (CBD)** | International Convention | 🌍 International | [CBD](https://www.cbd.int/) |
| 13 | **Nagoya Protocol on Access and Benefit-Sharing** | International Protocol | 🌍 International | [CBD](https://www.cbd.int/) |

---

## 🌐 Official Source Organizations

| Organization | Official Website | Purpose |
|---|---|---|
| **India Code** | [indiacode.nic.in](https://www.indiacode.nic.in/) | Primary source for Indian Central Acts |
| **IP India** | [ipindia.gov.in](https://www.ipindia.gov.in/) | Patent legislation and Patent Rules |
| **CDSCO** | [cdsco.gov.in](https://www.cdsco.gov.in/) | Drugs and Cosmetics regulatory material |
| **FSSAI** | [fssai.gov.in](https://www.fssai.gov.in/) | Food and Ayurveda Aahara regulations |
| **WTO** | [wto.org](https://www.wto.org/) | TRIPS Agreement |
| **Convention on Biological Diversity** | [cbd.int](https://www.cbd.int/) | CBD and Nagoya Protocol |

---

## 🔄 Corpus Processing Pipeline

The collected legal documents are processed through the following pipeline:

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
Structure-Aware Parsing
        │
        ▼
Section / Clause Chunking
        │
        ▼
Metadata Extraction
        │
        ├── Document Name
        ├── Section / Article
        ├── Jurisdiction
        ├── Document Type
        ├── Year
        └── Source URL
        │
        ▼
BM25 + Vector Embeddings
        │
        ▼
Chroma Vector Database
        │
        ▼
Hybrid Retrieval
        │
        ▼
Grounded Answer + Citations
```

---

## 🧾 Document Metadata

Each corpus document and its resulting chunks are associated with metadata such as:

- **Document name**
- **Document type**
- **Jurisdiction**
- **Year**
- **Section / Article number**
- **Source organization**
- **Official source URL**
- **Document version / effective date**

Example:

```json
{
  "title": "The Patents Act, 1970",
  "document_type": "Act",
  "jurisdiction": "India",
  "year": 1970,
  "section": "Section 3(p)",
  "source_organization": "India Code",
  "source_url": "https://www.indiacode.nic.in/"
}
```

### Judicial decisions (case law — roadmap S14)

Cases are ingested with `document_type: "case"`. They are retrieved alongside
the statute text but are **never a primary citation** — a court applies the
law, it is not the law's text. The backend surfaces them under a separate
"How courts have applied this" block.

```json
{
  "document_type": "case",
  "source": "Novartis AG v. Union of India",
  "citation": "(2013) 6 SCC 1",
  "court": "Supreme Court of India",
  "year": 2013,
  "section": "3(d)",
  "jurisdiction": "India",
  "source_url": "https://main.sci.gov.in/"
}
```

---

## 🎯 Purpose of the Corpus

The corpus serves as the **authoritative knowledge base** for IP-SAKTI Sahayak.

Instead of relying solely on an LLM's pretrained knowledge, the system retrieves relevant provisions from the corpus and provides them to the generation layer.

```text
User Query
    │
    ▼
Query Classification
    │
    ▼
Hybrid Retrieval
 ┌──┴──────────┐
 ▼             ▼
BM25        Chroma
 ▼             ▼
 └──────┬──────┘
        ▼
Relevant Legal Provisions
        │
        ▼
LLM Generation
        │
        ▼
Answer + Source Citations
```

This approach helps keep responses **grounded in the project's defined legal corpus** and enables users to trace answers back to the relevant legal provisions.

---

## ⚠️ Corpus Scope

The initial corpus is intentionally restricted to the legal and regulatory sources defined in the project's PRD.

Additional sources may be incorporated in future versions when required for:

- Expanded legal coverage
- Improved retrieval accuracy
- Additional jurisdictions
- New amendments or regulations
- Additional traditional-knowledge references

> **Source policy:** Prefer authoritative government and international-organization publications over third-party copies whenever an official source is available.

---

## 📌 Disclaimer

IP-SAKTI Sahayak is an **AI-assisted legal information and research system**. The retrieved information is intended for research and informational purposes and should not be treated as a substitute for professional legal advice.