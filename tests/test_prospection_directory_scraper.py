import pytest

from agents.prospection.compliance import ForbiddenSourceError
from agents.prospection.directory_scraper import fetch_directory_page


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        pass


class _FakeHttpClient:
    def __init__(self, text: str) -> None:
        self._text = text

    def get(self, url: str) -> _FakeResponse:
        return _FakeResponse(self._text)


def test_fetch_directory_page_parses_html() -> None:
    fake_client = _FakeHttpClient("<html><body><h1>Annuaire</h1></body></html>")

    soup = fetch_directory_page("https://annuaire-gabon.example/entreprises", http_client=fake_client)

    assert soup.find("h1").text == "Annuaire"


def test_fetch_directory_page_refuses_linkedin_before_any_request() -> None:
    class _ExplodingClient:
        def get(self, url: str):
            raise AssertionError("Ne doit jamais être appelé pour une source interdite")

    with pytest.raises(ForbiddenSourceError):
        fetch_directory_page("https://www.linkedin.com/company/example", http_client=_ExplodingClient())
