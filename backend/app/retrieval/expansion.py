"""Rule-based query expansion for retrieval.

The corpus is statute text; user questions use domain vocabulary that never
appears in the statute ("classical Ayurvedic formulation" vs. the Patents Act's
"traditional knowledge ... aggregation or duplication of known properties").
A small, explicit synonym-bridge map closes that gap before hybrid retrieval.

Deliberately rule-based and inspectable — same rationale as the classifier. The
expansion is appended ONLY to the retrieval query; the question shown to the user
and sent to the generator is untouched.
"""
from __future__ import annotations

import re

# (trigger_a, trigger_b, terms_to_append)
# Both triggers must match for the expansion to apply, so we only fire on a
# genuine topic overlap rather than on a stray keyword.
_RULES: list[tuple[re.Pattern[str], re.Pattern[str], str]] = [
    (
        re.compile(r"\bpatent(?:ed|able|ability|ing|s)?\b", re.I),
        re.compile(
            r"\b(ayurved\w*|classical|traditional|shastric|siddha|unani|"
            r"formulation|nghantu|nghigh|herbal|plant[- ]based)\b",
            re.I,
        ),
        "traditional knowledge; not an invention within the meaning of this Act; "
        "mere admixture aggregation or duplication of known properties of "
        "traditionally known components; what are not inventions section 3",
    ),
    (
        re.compile(r"\b(benefit[- ]shar\w*|abs|royalt\w*)\b", re.I),
        re.compile(r"\b(biological|genetic|resource|nba|biodiversity)\b", re.I),
        "fair and equitable benefit sharing determination National Biodiversity Authority",
    ),
    (
        re.compile(r"\b(advertis\w*|claim\w*|market\w*)\b", re.I),
        re.compile(r"\b(cure|disease|diabetes|treatment|remedy|therapeutic)\b", re.I),
        "prohibition of advertisement magic remedies objectionable diseases schedule",
    ),
]


def expand_query(query: str) -> str:
    """Return the query with domain-bridge terms appended where a rule fires."""
    extra: list[str] = []
    for trig_a, trig_b, terms in _RULES:
        if trig_a.search(query) and trig_b.search(query):
            extra.append(terms)
    if not extra:
        return query
    return f"{query} {' '.join(extra)}"
