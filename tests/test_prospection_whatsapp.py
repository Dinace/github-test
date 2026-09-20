import pytest

from agents.prospection.whatsapp import WhatsAppSendError, send_whatsapp_message


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
        self.calls: list[tuple[str, dict, dict]] = []

    def post(self, url: str, *, headers: dict, json: dict) -> _FakeResponse:
        self.calls.append((url, headers, json))
        return self._response


def test_send_whatsapp_message_returns_message_id() -> None:
    fake_client = _FakeHttpClient(_FakeResponse(200, {"messages": [{"id": "wamid.123"}]}))

    message_id = send_whatsapp_message(
        "1234567890", "fake-token", "+24101020304", "Bonjour !", http_client=fake_client
    )

    assert message_id == "wamid.123"
    url, headers, body = fake_client.calls[0]
    assert url == "https://graph.facebook.com/v19.0/1234567890/messages"
    assert headers["Authorization"] == "Bearer fake-token"
    assert body["to"] == "+24101020304"


def test_send_whatsapp_message_raises_on_http_error() -> None:
    fake_client = _FakeHttpClient(_FakeResponse(401, text="Invalid access token"))

    with pytest.raises(WhatsAppSendError):
        send_whatsapp_message("1234567890", "bad-token", "+24101020304", "Bonjour", http_client=fake_client)
