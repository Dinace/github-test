import httpx
import pytest

from agents.maintenance.security_headers import check_security_headers, classify_urgency


class _FakeResponse:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


class _FakeHttpClient:
    def __init__(self, response: _FakeResponse | None = None, *, exc: Exception | None = None) -> None:
        self._response = response
        self._exc = exc

    def get(self, url: str, **kwargs) -> _FakeResponse:
        if self._exc is not None:
            raise self._exc
        return self._response


_ALL_HEADERS_PRESENT = {
    "Strict-Transport-Security": "max-age=63072000",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "no-referrer",
}


def test_check_security_headers_detects_present_headers() -> None:
    client = _FakeHttpClient(_FakeResponse(_ALL_HEADERS_PRESENT))

    findings = check_security_headers("https://example.ga", http_client=client)

    assert all(f.present for f in findings)


def test_check_security_headers_detects_missing_headers() -> None:
    client = _FakeHttpClient(_FakeResponse({}))

    findings = check_security_headers("https://example.ga", http_client=client)

    assert all(not f.present for f in findings)
    assert {f.header for f in findings} == {
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Content-Security-Policy",
        "Referrer-Policy",
    }


def test_check_security_headers_propagates_network_errors() -> None:
    client = _FakeHttpClient(exc=httpx.ConnectTimeout("timeout"))

    with pytest.raises(httpx.ConnectTimeout):
        check_security_headers("https://example.ga", http_client=client)


def test_classify_urgency_splits_missing_headers_by_severity() -> None:
    findings = check_security_headers("https://example.ga", http_client=_FakeHttpClient(_FakeResponse({})))

    urgent, deferred = classify_urgency(findings)

    assert {f.header for f in urgent} == {"Strict-Transport-Security"}
    assert {f.header for f in deferred} == {
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Content-Security-Policy",
        "Referrer-Policy",
    }


def test_classify_urgency_ignores_present_headers() -> None:
    findings = check_security_headers(
        "https://example.ga", http_client=_FakeHttpClient(_FakeResponse(_ALL_HEADERS_PRESENT))
    )

    urgent, deferred = classify_urgency(findings)

    assert urgent == []
    assert deferred == []
