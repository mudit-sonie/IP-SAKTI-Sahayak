"""Rule-based formulation classifier (PRD section 2 — a 4-6 question decision tree).

Deliberately NOT an LLM. It's a small explainable decision tree so we can defend
every classification to a judge ("why is this 'proprietary' and not 'new drug'?").

Stateless: the frontend collects answers into a dict and posts the whole dict each
step; ``classify`` returns either the next question or a final category.

Answer keys map to the ``id`` of the question; answer values must be one of that
question's ``options`` (matched case-insensitively, on a substring, so the UI can
send either the full label or a short token).
"""
from __future__ import annotations

from dataclasses import dataclass

from app.schemas import ClassifyResponse, FormulationCategory, NextQuestion


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    options: list[str]


# --- Question bank -------------------------------------------------------- #
Q1 = Question(
    id="q1",
    text="What is the product's primary intended use?",
    options=[
        "Therapeutic / medicinal",
        "Food or nutraceutical (Ayurveda Aahara)",
        "Cosmetic / personal care",
    ],
)
Q2 = Question(
    id="q2",
    text=(
        "Is the formulation exactly as described in the authoritative Ayurveda "
        "texts listed in the First Schedule to the Drugs and Cosmetics Act "
        "(same ingredients, same proportions, same process)?"
    ),
    options=[
        "Yes - textual formulation, unchanged",
        "No - modified process, proportions or a new combination",
    ],
)
Q3 = Question(
    id="q3",
    text=(
        "Do all ingredients appear in the authoritative Ayurveda texts, even "
        "though the combination or indication is new?"
    ),
    options=[
        "Yes - all ingredients are textual",
        "No - includes a purified/standardised extract or a new chemical entity",
    ],
)
Q4 = Question(
    id="q4",
    text=(
        "Is the active a standardised extract or fraction of a plant "
        "(defined markers, characterised composition) rather than a single new "
        "synthetic molecule?"
    ),
    options=[
        "Yes - standardised botanical extract / fraction",
        "No - single new chemical entity or synthetic molecule",
    ],
)

QUESTIONS: dict[str, Question] = {q.id: q for q in (Q1, Q2, Q3, Q4)}


def _pick(answer: str, options: list[str]) -> int | None:
    """Return the index of the matched option, or None."""
    a = (answer or "").strip().lower()
    if not a:
        return None
    for i, opt in enumerate(options):
        ol = opt.lower()
        if a == ol or a in ol or ol.split(" - ")[0].strip() in a:
            return i
    # numeric answer ("1" / "2")
    if a.isdigit() and 1 <= int(a) <= len(options):
        return int(a) - 1
    return None


# Short label per question, for the decision-path explanation.
_SHORT = {
    "q1": "Intended use",
    "q2": "Textual formulation, unchanged",
    "q3": "All ingredients textual",
    "q4": "Standardised botanical extract",
}


def _next(question: Question) -> ClassifyResponse:
    return ClassifyResponse(
        next_question=NextQuestion(
            id=question.id, text=question.text, options=question.options
        ),
        complete=False,
    )


def _done(
    category: FormulationCategory, trail: list[tuple[str, int, list[str]]]
) -> ClassifyResponse:
    rationale = [
        f"{_SHORT[qid]}: {opts[idx]}" for qid, idx, opts in trail
    ]
    return ClassifyResponse(
        formulation_category=category, complete=True, rationale=rationale
    )


def classify(answers: dict[str, str]) -> ClassifyResponse:
    trail: list[tuple[str, int, list[str]]] = []

    a1 = _pick(answers.get("q1", ""), Q1.options)
    if a1 is None:
        return _next(Q1)
    trail.append(("q1", a1, Q1.options))
    if a1 == 2:
        return _done(FormulationCategory.cosmetic, trail)
    if a1 == 1:
        return _done(FormulationCategory.ayurveda_aahar, trail)

    # a1 == 0: therapeutic branch
    a2 = _pick(answers.get("q2", ""), Q2.options)
    if a2 is None:
        return _next(Q2)
    trail.append(("q2", a2, Q2.options))
    if a2 == 0:
        return _done(FormulationCategory.classical, trail)

    a3 = _pick(answers.get("q3", ""), Q3.options)
    if a3 is None:
        return _next(Q3)
    trail.append(("q3", a3, Q3.options))
    if a3 == 0:
        return _done(FormulationCategory.proprietary, trail)

    a4 = _pick(answers.get("q4", ""), Q4.options)
    if a4 is None:
        return _next(Q4)
    trail.append(("q4", a4, Q4.options))
    if a4 == 0:
        return _done(FormulationCategory.phytopharmaceutical, trail)
    return _done(FormulationCategory.new_drug, trail)
