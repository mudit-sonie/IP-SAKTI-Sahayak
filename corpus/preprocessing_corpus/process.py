import os
import re
import json
import hashlib
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF


# =========================
# SETTINGS
# =========================

INPUT_FOLDER = "pdfs"
OUTPUT_FOLDER = "cleaned_corpus"

MIN_PAGE_TEXT = 50
MIN_DOCUMENT_TEXT = 200


# =========================
# BASIC CLEANING
# =========================

def normalize_unicode(text):
    """
    Normalize Unicode characters.
    """
    text = unicodedata.normalize("NFKC", text)

    # Replace common special spaces
    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\u200c", "")
    text = text.replace("\u200d", "")

    return text


def clean_special_characters(text):
    """
    Remove unwanted control characters while keeping
    useful punctuation and newlines.
    """

    cleaned = []

    for char in text:
        category = unicodedata.category(char)

        # Keep normal characters
        if category.startswith("C"):
            if char in ("\n", "\t"):
                cleaned.append(char)
            continue

        cleaned.append(char)

    return "".join(cleaned)


def fix_hyphenated_words(text):
    """
    Fix words split across lines.

    Example:
        informa-
        tion

    becomes:
        information
    """

    text = re.sub(
        r"(\w)-\s*\n\s*(\w)",
        r"\1\2",
        text
    )

    return text


def fix_line_breaks(text):
    """
    Fix PDF line wrapping while preserving paragraphs.
    """

    # Normalize CRLF
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Remove spaces before newline
    text = re.sub(r"[ ]+\n", "\n", text)

    # Remove excessive spaces
    text = re.sub(r"[ ]{2,}", " ", text)

    # Join lines when the next line does not look like
    # a new paragraph.
    lines = text.split("\n")

    new_lines = []
    current = ""

    for line in lines:
        line = line.strip()

        if not line:
            if current:
                new_lines.append(current.strip())
                current = ""

            new_lines.append("")
            continue

        # If current line exists, decide whether to join
        if current:

            # Don't join if current line ends with punctuation
            # that normally indicates a sentence.
            if re.search(r"[.!?:;]$", current):
                new_lines.append(current.strip())
                current = line

            # Don't join headings / list items
            elif re.match(
                r"^(\d+[\.\)]|[-*•]|[A-Z][A-Z\s]{3,}$)",
                line
            ):
                new_lines.append(current.strip())
                current = line

            else:
                current += " " + line

        else:
            current = line

    if current:
        new_lines.append(current.strip())

    text = "\n".join(new_lines)

    return text


def clean_paragraphs(text):
    """
    Clean paragraph structure.
    """

    # Remove spaces around blank lines
    text = re.sub(r" *\n *\n *", "\n\n", text)

    # Maximum two newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove spaces at beginning/end
    text = text.strip()

    return text


# =========================
# HEADER / FOOTER REMOVAL
# =========================

def normalize_for_matching(text):
    """
    Used to compare headers and footers.
    """
    text = text.lower()
    text = re.sub(r"\d+", "#", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_repeated_lines(page_texts, min_occurrences=3):
    """
    Find lines that appear repeatedly across pages.

    These are often:
    - headers
    - footers
    - journal names
    - copyright text
    - repeated document titles
    """

    counts = {}

    for text in page_texts:

        lines = text.split("\n")

        # Only inspect first and last few lines
        candidates = lines[:5] + lines[-5:]

        seen_on_page = set()

        for line in candidates:

            line = line.strip()

            if len(line) < 5:
                continue

            normalized = normalize_for_matching(line)

            if normalized in seen_on_page:
                continue

            seen_on_page.add(normalized)

            counts[normalized] = counts.get(normalized, 0) + 1

    repeated = {
        line
        for line, count in counts.items()
        if count >= min_occurrences
    }

    return repeated


def remove_repeated_lines(text, repeated_lines):
    """
    Remove lines identified as repeated headers/footers.
    """

    result = []

    for line in text.split("\n"):

        normalized = normalize_for_matching(line)

        if normalized in repeated_lines:
            continue

        result.append(line)

    return "\n".join(result)


# =========================
# PAGE NUMBER REMOVAL
# =========================

def remove_page_numbers(text):
    """
    Remove common standalone page numbers.
    """

    text = re.sub(
        r"(?m)^\s*(page\s+)?\d+\s*$",
        "",
        text,
        flags=re.IGNORECASE
    )

    return text


# =========================
# URL / EMAIL CLEANING
# =========================

def clean_urls_and_emails(text):
    """
    Normalize URLs and email addresses.

    We don't completely remove them because they can contain
    useful information for AI models.
    """

    # Remove tracking-style URL spaces
    text = re.sub(
        r"https?\s*:\s*/\s*/",
        "https://",
        text,
        flags=re.IGNORECASE
    )

    # Fix spaces around @
    text = re.sub(
        r"\s*@\s*",
        "@",
        text
    )

    return text


# =========================
# OCR / PDF JUNK
# =========================

def remove_common_pdf_junk(text):
    """
    Remove common extraction artifacts.
    """

    # Repeated dots
    text = re.sub(r"\.{4,}", "...", text)

    # Repeated underscores
    text = re.sub(r"_{4,}", "", text)

    # Repeated dashes
    text = re.sub(r"-{5,}", "", text)

    # Common bullet variations
    text = text.replace("▪", "•")
    text = text.replace("◦", "•")
    text = text.replace("‣", "•")

    return text


# =========================
# MAIN TEXT CLEANER
# =========================

def clean_text(text, repeated_lines=None):

    if not text:
        return ""

    # Unicode
    text = normalize_unicode(text)

    # PDF artifacts
    text = clean_special_characters(text)

    # Headers and footers
    if repeated_lines:
        text = remove_repeated_lines(
            text,
            repeated_lines
        )

    # Page numbers
    text = remove_page_numbers(text)

    # URLs / emails
    text = clean_urls_and_emails(text)

    # PDF junk
    text = remove_common_pdf_junk(text)

    # Fix words split across lines
    text = fix_hyphenated_words(text)

    # Fix line wrapping
    text = fix_line_breaks(text)

    # Paragraph cleanup
    text = clean_paragraphs(text)

    return text


# =========================
# PDF EXTRACTION
# =========================

def extract_pdf(pdf_path):
    """
    Extract text page-by-page.
    """

    pages = []

    try:
        doc = fitz.open(pdf_path)

        for page_number, page in enumerate(doc):

            text = page.get_text("text")

            pages.append({
                "page": page_number + 1,
                "text": text
            })

        doc.close()

    except Exception as e:

        print(
            f"ERROR reading {pdf_path}: {e}"
        )

        return []

    return pages


# =========================
# DOCUMENT PROCESSING
# =========================

def process_pdf(pdf_path):

    print(f"Processing: {pdf_path.name}")

    pages = extract_pdf(pdf_path)

    if not pages:
        return None

    raw_page_texts = [
        page["text"]
        for page in pages
    ]

    # Find repeated headers / footers
    repeated_lines = find_repeated_lines(
        raw_page_texts,
        min_occurrences=3
    )

    cleaned_pages = []

    for page in pages:

        cleaned = clean_text(
            page["text"],
            repeated_lines
        )

        if len(cleaned.strip()) >= MIN_PAGE_TEXT:

            cleaned_pages.append({
                "page": page["page"],
                "text": cleaned
            })

    full_text = "\n\n".join(
        page["text"]
        for page in cleaned_pages
    )

    # Final cleaning
    full_text = clean_text(
        full_text
    )

    if len(full_text) < MIN_DOCUMENT_TEXT:
        print(
            f"  WARNING: very little text extracted "
            f"from {pdf_path.name}"
        )

    # Document ID
    doc_id = hashlib.md5(
        full_text.encode("utf-8")
    ).hexdigest()

    return {
        "id": doc_id,
        "filename": pdf_path.name,
        "source": pdf_path.name,
        "num_pages": len(pages),
        "pages_with_text": len(cleaned_pages),
        "character_count": len(full_text),
        "word_count": len(full_text.split()),
        "text": full_text
    }


# =========================
# DUPLICATE DETECTION
# =========================

def remove_duplicate_documents(documents):

    seen = set()
    unique_documents = []

    for doc in documents:

        text_hash = hashlib.sha256(
            doc["text"].encode("utf-8")
        ).hexdigest()

        if text_hash in seen:

            print(
                f"Duplicate removed: {doc['filename']}"
            )

            continue

        seen.add(text_hash)
        unique_documents.append(doc)

    return unique_documents


# =========================
# SAVE OUTPUT
# =========================

def save_documents(documents):

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    # -------------------------
    # Individual TXT files
    # -------------------------

    txt_folder = os.path.join(
        OUTPUT_FOLDER,
        "documents"
    )

    os.makedirs(
        txt_folder,
        exist_ok=True
    )

    for doc in documents:

        filename = Path(
            doc["filename"]
        ).stem

        output_path = os.path.join(
            txt_folder,
            filename + ".txt"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(doc["text"])

    # -------------------------
    # Combined corpus
    # -------------------------

    combined_path = os.path.join(
        OUTPUT_FOLDER,
        "cleaned_corpus.txt"
    )

    with open(
        combined_path,
        "w",
        encoding="utf-8"
    ) as f:

        for i, doc in enumerate(documents):

            f.write(
                f"\n\n{'=' * 80}\n"
            )

            f.write(
                f"SOURCE: {doc['filename']}\n"
            )

            f.write(
                f"{'=' * 80}\n\n"
            )

            f.write(
                doc["text"]
            )

            f.write("\n")

    # -------------------------
    # JSON corpus
    # -------------------------

    json_path = os.path.join(
        OUTPUT_FOLDER,
        "cleaned_corpus.json"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            documents,
            f,
            indent=2,
            ensure_ascii=False
        )

    # -------------------------
    # Statistics
    # -------------------------

    total_chars = sum(
        doc["character_count"]
        for doc in documents
    )

    total_words = sum(
        doc["word_count"]
        for doc in documents
    )

    stats = {
        "documents": len(documents),
        "total_pages": sum(
            doc["num_pages"]
            for doc in documents
        ),
        "pages_with_text": sum(
            doc["pages_with_text"]
            for doc in documents
        ),
        "total_characters": total_chars,
        "total_words": total_words
    }

    stats_path = os.path.join(
        OUTPUT_FOLDER,
        "statistics.json"
    )

    with open(
        stats_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            stats,
            f,
            indent=2
        )

    return stats


# =========================
# MAIN
# =========================

def main():

    print("\n==============================")
    print("PDF CORPUS PREPROCESSOR")
    print("==============================\n")

    input_path = Path(INPUT_FOLDER)

    if not input_path.exists():

        print(
            f"Input folder '{INPUT_FOLDER}' "
            f"does not exist."
        )

        return

    pdf_files = sorted(
        input_path.glob("*.pdf")
    )

    if not pdf_files:

        print(
            "No PDF files found."
        )

        return

    print(
        f"Found {len(pdf_files)} PDF files.\n"
    )

    documents = []

    for pdf_file in pdf_files:

        document = process_pdf(
            pdf_file
        )

        if document:
            documents.append(document)

    print("\nRemoving duplicates...")

    documents = remove_duplicate_documents(
        documents
    )

    print("\nSaving corpus...")

    stats = save_documents(
        documents
    )

    print("\n==============================")
    print("DONE")
    print("==============================")

    print(
        f"Documents: {stats['documents']}"
    )

    print(
        f"Pages: {stats['total_pages']}"
    )

    print(
        f"Pages with text: "
        f"{stats['pages_with_text']}"
    )

    print(
        f"Total words: "
        f"{stats['total_words']:,}"
    )

    print(
        f"Total characters: "
        f"{stats['total_characters']:,}"
    )

    print(
        f"\nOutput saved to: "
        f"{OUTPUT_FOLDER}/"
    )


if __name__ == "__main__":
    main()