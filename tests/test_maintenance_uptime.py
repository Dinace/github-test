from datetime import UTC, datetime, timedelta

from agents.maintenance.uptime import check_uptime, should_notify_downtime


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


class _FakeHttpClient:
    def __init__(self, status_code: int) -> None:
        self._status_code = status_code

    def post(self, url: str, data: dict) -> _FakeResponse:
        return _FakeResponse({"monitors": [{"status": self._status_code}]})


def test_check_uptime_reports_up() -> None:
    result = check_uptime("12345", http_client=_FakeHttpClient(2))
    assert result.is_up is True
    assert result.status_label == "up"


def test_check_uptime_reports_down() -> None:
    result = check_uptime("12345", http_client=_FakeHttpClient(9))
    assert result.is_up is False
    assert result.status_label == "down"


def test_should_notify_downtime_below_threshold() -> None:
    now = datetime.now(UTC)
    down_since = now - timedelta(minutes=10)
    assert should_notify_downtime(down_since, now) is False


def test_should_notify_downtime_above_threshold() -> None:
    now = datetime.now(UTC)
    down_since = now - timedelta(minutes=16)
    assert should_notify_downtime(down_since, now) is True
