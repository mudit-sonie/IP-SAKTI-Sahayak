"""Fee calculators (roadmap S11)."""


def test_fees_schedule_shape(client):
    body = client.get("/fees").json()
    assert body["disclaimer"]
    tracks = {s["track"] for s in body["schedules"]}
    assert tracks == {"patent", "gi"}
    patent = next(s for s in body["schedules"] if s["track"] == "patent")
    assert patent["renewal_bands"]
    assert {e["key"] for e in patent["entities"]} == {
        "individual_startup_small", "others",
    }


def test_estimate_sums_items(client):
    r = client.post(
        "/fees/estimate",
        json={
            "track": "patent",
            "entity": "individual_startup_small",
            "item_codes": ["filing", "rfe"],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1600 + 4000
    assert body["currency"] == "INR"


def test_estimate_renewal_bands_span(client):
    r = client.post(
        "/fees/estimate",
        json={
            "track": "patent",
            "entity": "others",
            "item_codes": [],
            "renewal_from_year": 3,
            "renewal_to_year": 10,
        },
    )
    body = r.json()
    # years 3-6 (4y @ 4000) + 7-10 (4y @ 12000)
    assert body["total"] == 4 * 4000 + 4 * 12000
    assert body["lines"][0]["code"] == "renewal"


def test_estimate_unknown_entity_rejected(client):
    r = client.post(
        "/fees/estimate",
        json={"track": "patent", "entity": "nope", "item_codes": ["filing"]},
    )
    assert r.status_code == 422


def test_estimate_gi(client):
    r = client.post(
        "/fees/estimate",
        json={
            "track": "gi",
            "entity": "standard",
            "item_codes": ["gi_application", "gi_renewal"],
        },
    )
    assert r.json()["total"] == 10000
