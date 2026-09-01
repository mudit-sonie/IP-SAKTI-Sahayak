"""Answer translation scaffold (roadmap S15)."""


def test_languages_lists_english_and_indian_langs(client):
    langs = client.get("/languages").json()
    codes = {x["code"] for x in langs}
    assert "en" in codes and "hi" in codes and "ta" in codes


def test_translate_falls_back_to_english_without_gemini(client):
    # CI has no Gemini key -> honest fallback, never a fabricated translation
    r = client.post(
        "/translate", json={"text": "A patent lasts 20 years. [1]", "lang": "hi"}
    )
    assert r.status_code == 200
    body = r.json()
    if not body["translated"]:
        assert body["lang"] == "en"
        assert body["text"] == "A patent lasts 20 years. [1]"


def test_translate_noop_for_english(client):
    r = client.post("/translate", json={"text": "hello", "lang": "en"}).json()
    assert r["translated"] is False
    assert r["text"] == "hello"


def test_translate_unknown_lang_is_fallback(client):
    r = client.post("/translate", json={"text": "hello", "lang": "xx"}).json()
    assert r["translated"] is False
