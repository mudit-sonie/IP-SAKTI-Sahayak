"""Text extraction for matter documents (roadmap S20)."""
import io

import pytest

from app.services.doc_extract import ExtractionError, extract


def test_txt_and_md():
    text, media, pages = extract("notes.txt", b"hello world")
    assert text == "hello world" and media == "text/plain" and pages is None
    _, media_md, _ = extract("notes.md", b"# Title")
    assert media_md == "text/markdown"


def test_unsupported_extension():
    with pytest.raises(ExtractionError):
        extract("archive.zip", b"PK\x03\x04")


def test_docx_roundtrip():
    docx = pytest.importorskip("docx")
    d = docx.Document()
    d.add_paragraph("Draft claim 1: a standardised extract.")
    d.add_paragraph("Draft claim 2: a spray-drying step.")
    buf = io.BytesIO()
    d.save(buf)

    text, media, _ = extract("claims.docx", buf.getvalue())
    assert "spray-drying" in text
    assert "wordprocessingml" in media


def test_pdf_with_text_layer():
    pytest.importorskip("pypdf")
    from pypdf import PdfWriter

    # a blank page has no text layer -> should raise the scanned-PDF error
    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    w.write(buf)
    with pytest.raises(ExtractionError, match="scanned"):
        extract("blank.pdf", buf.getvalue())
