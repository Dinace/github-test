"""Tâches planifiées de l'agent Maintenance : sauvegarde + rétention, scan de sécurité,
vérification de disponibilité. Comblent le point ouvert "rien ne se déclenche
automatiquement, tout passe par un appel manuel à l'API" (agents/maintenance/skills/
README.md) — enregistrées dans `platform_core/scheduler.py`.

Décision actée dans cette session (pas tranchée avant) : la sauvegarde et le scan de
sécurité portent sur une ressource **partagée par toute la plateforme** (un seul `pg_dump`
de toute la base, un seul scan `pip-audit` des dépendances du code) — il n'existe pas de
notion "par client" pour ces deux-là, contrairement à la surveillance de disponibilité (un
monitor par site). Leur cadence suit donc l'abonnement actif le plus exigeant (Premium >
Business > Starter), pas une moyenne ni un calcul par client : servir le client Premium le
plus exigeant couvre de fait les besoins de tous les clients moins exigeants.
"""

from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from agents.maintenance import backup as backup_module
from agents.maintenance import security_scan as security_scan_module
from agents.maintenance import uptime as uptime_module
from platform_core.models import (
    Backup,
    Client,
    Notification,
    NotificationCategory,
    NotificationSeverity,
    NotificationStatus,
    Pack,
    Site,
    SiteStatus,
    Subscription,
)

# Uptime : cadence par pack (CLAUDE.md §1). "Temps réel" (Premium) approximé à 1 minute —
# aucune vraie infrastructure de push/webhook de monitoring temps réel dans cette session.
_UPTIME_INTERVALS: dict[Pack, timedelta] = {
    Pack.starter: timedelta(minutes=30),
    Pack.business: timedelta(minutes=5),
    Pack.premium: timedelta(minutes=1),
}

_BACKUP_INTERVALS: dict[Pack, timedelta] = {
    Pack.starter: timedelta(days=30),
    Pack.business: timedelta(days=7),
    Pack.premium: timedelta(days=1),
}

# Starter n'inclut pas le scan de sécurité (CLAUDE.md §1) : volontairement absent de ce dict.
_SECURITY_SCAN_INTERVALS: dict[Pack, timedelta] = {
    Pack.business: timedelta(days=30),
    Pack.premium: timedelta(days=7),
}


def _active_packs(db: Session) -> set[Pack]:
    return {s.pack for s in db.query(Subscription).filter(Subscription.active.is_(True)).all()}


def _now_naive_utc() -> datetime:
    """Les colonnes `DateTime` de `platform_core/models.py` sont sans fuseau (`TIMESTAMP
    WITHOUT TIME ZONE` sur PostgreSQL, comportement identique sur SQLite) : une valeur
    aware y perd son tzinfo à l'écriture comme à la lecture. Comparer un "now" aware à une
    valeur relue lève `TypeError` (offset-naive vs offset-aware) — toute cette arithmétique
    de dates utilise donc une convention naïve-mais-UTC, cohérente avec ce que les colonnes
    contiennent réellement une fois rechargées depuis la base."""
    return datetime.now(UTC).replace(tzinfo=None)


def run_backups_and_retention(session_factory: Callable[[], AbstractContextManager[Session]]) -> None:
    with session_factory() as db:
        active_packs = _active_packs(db)
        pack = next((p for p in (Pack.premium, Pack.business, Pack.starter) if p in active_packs), None)
        if pack is None:
            return  # aucun abonnement actif : rien à sauvegarder.

        last_backup = db.query(Backup).order_by(Backup.created_at.desc()).first()
        if last_backup is not None and _now_naive_utc() - last_backup.created_at < _BACKUP_INTERVALS[pack]:
            return

        # Aware ici (pas `_now_naive_utc()`) : passé à agents/maintenance/backup.py, qui
        # parse les clés R2 en datetimes aware (`_parse_backup_timestamp`) — un "now" naïf y
        # lèverait la même TypeError offset-naive/offset-aware, dans l'autre sens.
        now_aware = datetime.now(UTC)
        try:
            dump = backup_module.create_backup()
            key = backup_module.upload_backup(dump, now_aware)
        except Exception as exc:  # noqa: BLE001 — toute panne de backup doit notifier, jamais échouer en silence
            db.add(
                Notification(
                    category=NotificationCategory.backup_failure,
                    severity=NotificationSeverity.critical,
                    message=f"Échec de la sauvegarde planifiée : {exc}",
                )
            )
            db.commit()
            return

        db.add(Backup(r2_key=key, size_bytes=len(dump)))
        backup_module.apply_retention(pack, now=now_aware)
        db.commit()


def run_security_scans(session_factory: Callable[[], AbstractContextManager[Session]]) -> None:
    with session_factory() as db:
        active_packs = _active_packs(db)
        pack = next((p for p in (Pack.premium, Pack.business) if p in active_packs), None)
        if pack is None:
            return  # ni Business ni Premium actif : le scan de sécurité n'est dû à personne.

        last_scan = (
            db.query(Notification)
            .filter(Notification.category == NotificationCategory.security_finding)
            .order_by(Notification.created_at.desc())
            .first()
        )
        if last_scan is not None and _now_naive_utc() - last_scan.created_at < _SECURITY_SCAN_INTERVALS[pack]:
            return

        findings = security_scan_module.run_pip_audit()
        urgent, deferred = security_scan_module.classify_urgency(findings)

        # Une notification "aucune vulnérabilité" est créée même sans trouvaille : c'est ce
        # qui permet de savoir quand le dernier scan a effectivement tourné (pas de table de
        # log de scan dédiée), sans quoi ce job re-scannerait à chaque tick indéfiniment.
        if not findings:
            db.add(
                Notification(
                    category=NotificationCategory.security_finding,
                    severity=NotificationSeverity.info,
                    message="Scan de sécurité (pip-audit) exécuté : aucune vulnérabilité détectée.",
                )
            )
        if urgent:
            db.add(
                Notification(
                    category=NotificationCategory.security_finding,
                    severity=NotificationSeverity.critical,
                    message=(
                        f"{len(urgent)} vulnérabilité(s) haute/critique détectée(s) : "
                        + "; ".join(f"{f.package} ({f.vulnerability_id})" for f in urgent[:10])
                    ),
                )
            )
        if deferred:
            db.add(
                Notification(
                    category=NotificationCategory.security_finding,
                    severity=NotificationSeverity.info,
                    message=(
                        f"{len(deferred)} vulnérabilité(s) faible/moyenne (résumé de la période) : "
                        + "; ".join(f"{f.package} ({f.vulnerability_id})" for f in deferred[:10])
                    ),
                )
            )
        db.commit()


def run_uptime_checks(session_factory: Callable[[], AbstractContextManager[Session]]) -> None:
    with session_factory() as db:
        now = _now_naive_utc()
        sites = (
            db.query(Site)
            .filter(Site.status == SiteStatus.published, Site.uptime_monitor_id.isnot(None))
            .all()
        )

        for site in sites:
            subscription = (
                db.query(Subscription)
                .filter(Subscription.client_id == site.client_id, Subscription.active.is_(True))
                .first()
            )
            pack = subscription.pack if subscription is not None else Pack.starter
            interval = _UPTIME_INTERVALS[pack]
            if site.last_uptime_check_at is not None and now - site.last_uptime_check_at < interval:
                continue

            try:
                result = uptime_module.check_uptime(site.uptime_monitor_id)
            except Exception:  # noqa: BLE001 — panne de l'appel API lui-même, pas "site down" : réessayé au prochain tick
                continue

            site.last_uptime_check_at = now
            if result.is_up:
                site.down_since = None
                continue

            if site.down_since is None:
                site.down_since = now
                continue

            if not uptime_module.should_notify_downtime(site.down_since, now):
                continue

            already_notified = (
                db.query(Notification)
                .filter(
                    Notification.site_id == site.id,
                    Notification.category == NotificationCategory.site_down,
                    Notification.status == NotificationStatus.pending,
                )
                .first()
            )
            if already_notified is None:
                client = db.get(Client, site.client_id)
                db.add(
                    Notification(
                        category=NotificationCategory.site_down,
                        severity=NotificationSeverity.critical,
                        message=f"Le site de {client.name} est injoignable depuis plus de 15 minutes.",
                        client_id=site.client_id,
                        site_id=site.id,
                    )
                )

        db.commit()
