import httpx

from agents.prospection.scoring import WebsiteStatus
from agents.prospection.website_audit import assess_website

_MODERN_HTML = (
    "<html><head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
    "</head><body>" + "<p>Contenu du site.</p>" * 50 + "</body></html>"
)

_NO_VIEWPORT_HTML = "<html><head></head><body>" + "<p>Vieux site sans balise viewport.</p>" * 50 + "</body></html>"

_TINY_HTML = "<html><body>En construction</body></html>"


class _FakeResponse:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text


class _FakeHttpClient:
    def __init__(self, response: _FakeResponse | None = None, *, exc: Exception | None = None) -> None:
        self._response = response
        self._exc = exc

    def get(self, url: str, **kwargs) -> _FakeResponse:
        if self._exc is not None:
            raise self._exc
        return self._response


def test_assess_website_modern_site_with_viewport() -> None:
    client = _FakeHttpClient(_FakeResponse(200, _MODERN_HTML))

    assert assess_website("https://example.ga", http_client=client) == WebsiteStatus.modern


def test_assess_website_without_viewport_is_outdated() -> None:
    client = _FakeHttpClient(_FakeResponse(200, _NO_VIEWPORT_HTML))

    assert assess_website("https://example.ga", http_client=client) == WebsiteStatus.outdated


def test_assess_website_tiny_page_is_outdated() -> None:
    client = _FakeHttpClient(_FakeResponse(200, _TINY_HTML))

    assert assess_website("https://example.ga", http_client=client) == WebsiteStatus.outdated


def test_assess_website_http_error_status_is_none() -> None:
    client = _FakeHttpClient(_FakeResponse(404, "Not found"))

    assert assess_website("https://example.ga", http_client=client) == WebsiteStatus.none


def test_assess_website_network_error_is_none() -> None:
    client = _FakeHttpClient(exc=httpx.ConnectTimeout("timeout"))

    assert assess_website("https://example.ga", http_client=client) == WebsiteStatus.none
