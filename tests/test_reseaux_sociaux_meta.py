import pytest

from agents.reseaux_sociaux.meta import MetaPublishError, publish_to_meta


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


class _FakeHttpClient:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.calls: list[tuple[str, dict]] = []

    def post(self, url: str, data: dict) -> _FakeResponse:
        self.calls.append((url, data))
        return self._response


def test_publish_to_meta_returns_post_id_on_success() -> None:
    fake_client = _FakeHttpClient(_FakeResponse(200, {"id": "123456_789"}))

    post_id = publish_to_meta("123456", "fake-token", "Bonjour Gabon !", http_client=fake_client)

    assert post_id == "123456_789"
    url, data = fake_client.calls[0]
    assert url == "https://graph.facebook.com/v19.0/123456/feed"
    assert data == {"message": "Bonjour Gabon !", "access_token": "fake-token"}


def test_publish_to_meta_raises_on_http_error() -> None:
    fake_client = _FakeHttpClient(_FakeResponse(400, text="Invalid OAuth access token"))

    with pytest.raises(MetaPublishError):
        publish_to_meta("123456", "expired-token", "Bonjour", http_client=fake_client)
