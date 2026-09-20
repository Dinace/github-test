"""Sauvegardes de la base de données PostgreSQL et politique de rétention.

pg_dump et l'upload R2 nécessitent une vraie connexion Postgres/R2, non disponible dans cet
environnement — même limite assumée que pour agents/creation_site/storage.py : le
sous-processus et le client S3 sont injectables, testés avec des doublures, pas vérifiés en
conditions réelles.
"""

import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from platform_core.config import settings
from platform_core.models import Pack

_BACKUP_PREFIX = "backups/"


def create_backup(*, run_command: Callable[..., subprocess.CompletedProcess] | None = None) -> bytes:
    """Exécute pg_dump et retourne le contenu du dump (format SQL texte)."""
    run_command = run_command or subprocess.run
    result = run_command(
        ["pg_dump", "--no-owner", "--format=plain", settings.database_url],
        capture_output=True,
        check=True,
    )
    return result.stdout


def _backup_key(timestamp: datetime) -> str:
    return f"{_BACKUP_PREFIX}{timestamp.strftime('%Y%m%dT%H%M%SZ')}.sql"


def _parse_backup_timestamp(key: str) -> datetime:
    raw = key.removeprefix(_BACKUP_PREFIX).removesuffix(".sql")
    return datetime.strptime(raw, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)


def upload_backup(data: bytes, timestamp: datetime, *, s3_client: Any = None) -> str:
    from agents.creation_site.storage import get_r2_client  # même bucket/credentials R2

    s3_client = s3_client or get_r2_client()
    key = _backup_key(timestamp)
    s3_client.put_object(Bucket=settings.cloudflare_r2_bucket, Key=key, Body=data, ContentType="application/sql")
    return key


def list_backup_keys(*, s3_client: Any = None) -> list[str]:
    from agents.creation_site.storage import get_r2_client

    s3_client = s3_client or get_r2_client()
    response = s3_client.list_objects_v2(Bucket=settings.cloudflare_r2_bucket, Prefix=_BACKUP_PREFIX)
    return [obj["Key"] for obj in response.get("Contents", [])]


def _period_key(dt: datetime, *, weekly: bool) -> tuple[int, int]:
    if weekly:
        iso = dt.isocalendar()
        return (iso.year, iso.week)
    return (dt.year, dt.month)


def _most_recent_per_period(entries: list[tuple[str, datetime]], *, weekly: bool) -> set[str]:
    """Regroupe par semaine ISO ou par mois calendaire, garde la plus récente entrée de
    chaque groupe — c'est la dérivation "un backup représentatif par période" du grand-père/
    père/fils (agents/maintenance/skills/README.md)."""
    best: dict[tuple[int, int], tuple[str, datetime]] = {}
    for key, dt in entries:
        period = _period_key(dt, weekly=weekly)
        if period not in best or dt > best[period][1]:
            best[period] = (key, dt)
    return {key for key, _ in best.values()}


def keys_to_retain(pack: Pack, keys: list[str], *, now: datetime) -> set[str]:
    """Applique la politique de rétention par pack (agents/maintenance/skills/README.md).

    Fonction pure, sans I/O : retourne l'ensemble des clés à CONSERVER parmi celles
    fournies. Le reste doit être supprimé (voir apply_retention).
    """
    entries = [(key, _parse_backup_timestamp(key)) for key in keys]

    def age_days(dt: datetime) -> float:
        return (now - dt).total_seconds() / 86400

    if pack == Pack.starter:
        # 3 dernières sauvegardes mensuelles (~3 mois).
        window = [(k, dt) for k, dt in entries if age_days(dt) <= 93]
        return _most_recent_per_period(window, weekly=False)

    if pack == Pack.business:
        # 8 dernières hebdomadaires (~2 mois) + 3 derniers mois en mensuel dérivé au-delà.
        weekly_window = [(k, dt) for k, dt in entries if age_days(dt) <= 56]
        monthly_window = [(k, dt) for k, dt in entries if 56 < age_days(dt) <= 56 + 93]
        return _most_recent_per_period(weekly_window, weekly=True) | _most_recent_per_period(
            monthly_window, weekly=False
        )

    # Premium : 30 derniers jours + 12 semaines dérivées + 6 mois dérivés au-delà.
    daily_window = {k for k, dt in entries if age_days(dt) <= 30}
    weekly_window = [(k, dt) for k, dt in entries if 30 < age_days(dt) <= 30 + 84]
    monthly_window = [(k, dt) for k, dt in entries if 30 + 84 < age_days(dt) <= 30 + 84 + 183]
    return (
        daily_window
        | _most_recent_per_period(weekly_window, weekly=True)
        | _most_recent_per_period(monthly_window, weekly=False)
    )


def apply_retention(pack: Pack, *, s3_client: Any = None, now: datetime | None = None) -> list[str]:
    """Supprime les sauvegardes hors fenêtre de rétention. Retourne les clés supprimées."""
    from agents.creation_site.storage import get_r2_client

    s3_client = s3_client or get_r2_client()
    now = now or datetime.now(UTC)
    keys = list_backup_keys(s3_client=s3_client)
    retain = keys_to_retain(pack, keys, now=now)

    deleted = [key for key in keys if key not in retain]
    for key in deleted:
        s3_client.delete_object(Bucket=settings.cloudflare_r2_bucket, Key=key)
    return deleted
