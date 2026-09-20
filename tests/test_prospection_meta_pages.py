import pytest

from agents.prospection.sources.meta_pages import search_pages
from platform_core.config import settings


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

    def get(self, url: str, *, params: dict) -> _FakeResponse:
        self.calls.append((url, params))
        return _FakeResponse(self._payload)


_SAMPLE_PAYLOAD = {
    "data": [
        {
            "name": "Boutique Chez Awa",
            "phone": "+24101020304",
            "website": "https://chez-awa.example",
            "location": {"street": "Rue du Marché", "city": "Libreville", "country": "Gabon"},
            "overall_star_rating": 4.2,
            "rating_count": 8,
            # "link" (URL de la Page Facebook elle-même) volontairement présent pour vérifier
            # qu'il n'est jamais confondu avec "website".
            "link": "https://facebook.com/chezawa",
        },
        {"name": "Boutique Sans Site"},
    ]
}


@pytest.fixture(autouse=True)
def _configured_meta_app(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "meta_app_id", "test-app-id")
    monkeypatch.setattr(settings, "meta_app_secret", "test-app-secret")


def test_search_pages_parses_results_and_uses_website_not_link() -> None:
    fake_client = _FakeHttpClient(_SAMPLE_PAYLOAD)

    results = search_pages("boutique Libreville", http_client=fake_client)

    assert len(results) == 2
    assert results[0].name == "Boutique Chez Awa"
    assert results[0].phone_number == "+24101020304"
    assert results[0].website_uri == "https://chez-awa.example"
    assert results[0].formatted_address == "Rue du Marché, Libreville, Gabon"
    assert results[1].name == "Boutique Sans Site"
    assert results[1].phone_number is None


def test_search_pages_sends_app_access_token() -> None:
    fake_client = _FakeHttpClient({"data": []})

    search_pages("boutique Port-Gentil", http_client=fake_client)

    _url, params = fake_client.calls[0]
    assert params["q"] == "boutique Port-Gentil"
    assert params["access_token"] == "test-app-id|test-app-secret"


def test_search_pages_returns_empty_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "meta_app_id", "")
    monkeypatch.setattr(settings, "meta_app_secret", "")
    fake_client = _FakeHttpClient({"data": [{"name": "Ne doit jamais être vu"}]})

    results = search_pages("boutique Libreville", http_client=fake_client)

    assert results == []
    assert fake_client.calls == []
