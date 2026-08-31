"""High-stakes question guard.

Freedom-to-operate, infringement, and "should I sue / am I liable" questions
carry legal risk that a retrieval-grounded summary must not answer, however
confident the retrieval looks. These always escalate to a human — see
PRODUCT_ROADMAP.md S17.
"""
from __future__ import annotations

import re

# Phrases that make a question fact-specific legal advice rather than a
# "what does the statute say" lookup.
_HIGH_STAKES = [
    r"freedom to operate",
    r"\bfto\b",
    r"\binfring(e|ing|ement)\b",
    r"am i (allowed|permitted|liable|infringing)",
    r"can i be sued",
    r"should i sue",
    r"will i (get|be) sued",
    r"is (this|my product|my formulation) legal",
    r"do i have a case",
    r"cease and desist",
    # opinion on *our own* product, not "what does the statute say"
    r"\b(is|are) (this|my|our|these|it) .{0,40}(patentable|infringing|legal|allowed)",
    r"\bcan (i|we) patent (this|my|our|it|these)\b",
    r"\bwill (this|my|our) .{0,40}(be granted|pass|survive)",
    r"does (this|my|our) .{0,40}(violate|infringe|breach)",
]

_PATTERN = re.compile("|".join(_HIGH_STAKES), re.IGNORECASE)

ESCALATE_NOTE = (
    "This looks like a freedom-to-operate, infringement, or fact-specific "
    "risk question. IP-SAKTI does not answer these from retrieval — the "
    "assessment depends on claim construction, prior art, and facts outside "
    "our corpus. A human IP facilitator should take this on."
)


def is_high_stakes(query: str) -> bool:
    return bool(_PATTERN.search(query or ""))
