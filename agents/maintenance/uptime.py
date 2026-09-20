"""Surveillance de disponibilité des sites clients via UptimeRobot."""

from dataclasses import dataclass
from datetime import datetime

import httpx

from platform_core.config import settings

_API_BASE = "https://api.uptimerobot.com/v2"

# https://uptimerobot.com/api/ — codes de statut d'un monitor.
_STATUS_LABELS = {
    0: "paused",
    1: "not_checked_yet",
    2: "up",
    8: "seems_down",
    9: "down",
}


@dataclass
class UptimeCheckResult:
    is_up: bool
    status_label: str


def check_uptime(monitor_id: str, *, http_client: httpx.Client | None = None) -> UptimeCheckResult:
    client = http_client or httpx.Client()
    response = client.post(
        f"{_API_BASE}/getMonitors",
        data={"api_key": settings.uptime_monitor_token, "monitors": monitor_id, "format": "json"},
    )
    response.raise_for_status()
    payload = response.json()
    monitor = payload["monitors"][0]
    status_code = monitor["status"]
    return UptimeCheckResult(is_up=status_code == 2, status_label=_STATUS_LABELS.get(status_code, "unknown"))


def should_notify_downtime(down_since: datetime, now: datetime) -> bool:
    """Seuil de notification humaine : 15 minutes d'indisponibilité consécutive
    (agents/maintenance/skills/README.md) — absorbe un aléa réseau ponctuel."""
    return (now - down_since).total_seconds() >= 15 * 60
