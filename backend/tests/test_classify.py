import pytest

from app.services.classifier import classify


def test_first_call_returns_q1():
    res = classify({})
    assert res.complete is False
    assert res.next_question.id == "q1"


def test_cosmetic_short_circuits():
    res = classify({"q1": "Cosmetic / personal care"})
    assert res.complete is True
    assert res.formulation_category.value == "cosmetic"


def test_food_maps_to_ayurveda_aahar():
    res = classify({"q1": "Food or nutraceutical (Ayurveda Aahara)"})
    assert res.formulation_category.value == "ayurveda_aahar"


def test_classical_path():
    res = classify({"q1": "Therapeutic / medicinal", "q2": "Yes - textual formulation, unchanged"})
    assert res.formulation_category.value == "classical"


def test_proprietary_path():
    res = classify(
        {
            "q1": "Therapeutic / medicinal",
            "q2": "No - modified process, proportions or a new combination",
            "q3": "Yes - all ingredients are textual",
        }
    )
    assert res.formulation_category.value == "proprietary"


@pytest.mark.parametrize(
    "q4,expected",
    [
        ("Yes - standardised botanical extract / fraction", "phytopharmaceutical"),
        ("No - single new chemical entity or synthetic molecule", "new_drug"),
    ],
)
def test_extract_vs_new_molecule(q4, expected):
    res = classify(
        {
            "q1": "Therapeutic / medicinal",
            "q2": "No",
            "q3": "No - includes a purified/standardised extract or a new chemical entity",
            "q4": q4,
        }
    )
    assert res.formulation_category.value == expected


def test_numeric_answers_accepted():
    res = classify({"q1": "1", "q2": "1"})
    assert res.formulation_category.value == "classical"


def test_rationale_traces_the_path():
    res = classify(
        {
            "q1": "Therapeutic / medicinal",
            "q2": "No - modified process, proportions or a new combination",
            "q3": "Yes - all ingredients are textual",
        }
    )
    assert res.formulation_category.value == "proprietary"
    assert len(res.rationale) == 3
    assert res.rationale[0].startswith("Intended use:")
    # in-progress responses carry no rationale
    assert classify({}).rationale == []
