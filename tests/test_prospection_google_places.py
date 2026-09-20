from agents.prospection.sources.google_places import search_places


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


class _FakeHttpClient:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.calls: list[tuple[str, dict]] = []

    def post(self, url: str, *, json: dict, headers: dict) -> _FakeResponse:
        self.calls.append((url, json))
        return _FakeResponse(self._payload)


_SAMPLE_PAYLOAD = {
    "places": [
        {
            "displayName": {"text": "Restaurant Chez Awa"},
            "formattedAddress": "Libreville, Gabon",
            "nationalPhoneNumber": "+24101020304",
            "websiteUri": "https://chez-awa.example",
            "rating": 4.5,
            "userRatingCount": 12,
        },
        {"displayName": {"text": "Boutique Sans Site"}},
    ]
}


def test_search_places_parses_results() -> None:
    fake_client = _FakeHttpClient(_SAMPLE_PAYLOAD)

    results = search_places("restaurant Libreville", http_client=fake_client)

    assert len(results) == 2
    assert results[0].name == "Restaurant Chez Awa"
    assert results[0].phone_number == "+24101020304"
    assert results[0].website_uri == "https://chez-awa.example"
    assert results[1].name == "Boutique Sans Site"
    assert results[1].phone_number is None


def test_search_places_sends_text_query() -> None:
    fake_client = _FakeHttpClient({"places": []})

    search_places("boutique Port-Gentil", http_client=fake_client)

    url, body = fake_client.calls[0]
    assert body == {"textQuery": "boutique Port-Gentil"}
