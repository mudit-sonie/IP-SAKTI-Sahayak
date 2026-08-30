"""Jurisdiction mismatch guard."""
from app.services.jurisdiction import mismatch_note


def test_india_question_under_international_toggle():
    note = mismatch_note("Can I patent this under the Patents Act, 1970 in India?", "international")
    assert note and "India" in note


def test_trips_question_under_india_toggle():
    note = mismatch_note("What does TRIPS Article 27 require?", "india")
    assert note and "International" in note


def test_no_note_when_aligned():
    assert mismatch_note("Can I patent this in India?", "india") is None
    assert mismatch_note("What does the CBD say about ABS?", "international") is None


def test_no_note_when_ambiguous():
    assert mismatch_note("How long does a patent last?", "india") is None
