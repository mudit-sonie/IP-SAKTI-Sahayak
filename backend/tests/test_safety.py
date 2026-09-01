from app.services.safety import is_high_stakes


def test_flags_fto_and_infringement():
    assert is_high_stakes("Do we have freedom to operate for this blend?")
    assert is_high_stakes("Is my product infringing the Patanjali patent?")
    assert is_high_stakes("Can I be sued for selling this churna?")
    assert is_high_stakes("Is our formulation patentable?")
    assert is_high_stakes("Does my product violate the Biodiversity Act?")


def test_allows_plain_statute_lookups():
    assert not is_high_stakes("Can a classical Ayurvedic formulation be patented in India?")
    assert not is_high_stakes("What is the term of a patent in India?")
    assert not is_high_stakes("What does section 3(p) of the Patents Act say?")
    assert not is_high_stakes("Do I need NBA approval before filing a patent using a biological resource?")
