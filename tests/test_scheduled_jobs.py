import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agents.maintenance import backup as backup_module
from agents.maintenance import scheduled_jobs as maintenance_jobs
from agents.maintenance import security_scan as security_scan_module
from agents.maintenance import uptime as uptime_module
from agents.planning import scheduled_jobs as planning_jobs
from agents.prospection import whatsapp as whatsapp_module
from agents.reseaux_sociaux import agent as post_agent
from agents.reseaux_sociaux import scheduled_jobs as posts_jobs
from platform_core.config import settings
from platform_core.db import Base
from platform_core.models import (
    Appointment,
    AppointmentStatus,
    Client,
    Notification,
    NotificationCategory,
    Pack,
    Post,
    PostStatus,
    Site,
    SiteStatus,
    Subscription,
)


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _make_client(session_factory, *, pack: Pack | None = None, **kwargs) -> uuid.UUID:
    """Retourne l'id du client créé (pas l'objet ORM, qui serait détaché dès la sortie du
    `with` ci-dessous — toute relecture d'attribut lèverait `DetachedInstanceError`)."""
    with session_factory() as db:
        client = Client(name="Chez Awa", sector="restaurant", api_key_hash=uuid.uuid4().hex, **kwargs)
        db.add(client)
        db.commit()
        db.refresh(client)
        client_id = client.id
        if pack is not None:
            db.add(Subscription(client_id=client_id, pack=pack, price_amount=1000, payment_provider="orange_money"))
            db.commit()
        return client_id


# --- Réseaux sociaux : publish_due_posts ------------------------------------------------


def test_publish_due_posts_publishes_and_marks_published(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(session_factory, meta_page_id="page-1", meta_page_access_token="token-1")
    with session_factory() as db:
        post = Post(
            client_id=client,
            brief={},
            content={"caption": "Promo du jour", "hashtags": ["gabon"]},
            status=PostStatus.scheduled,
            scheduled_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        db.add(post)
        db.commit()
        post_id = post.id

    monkeypatch.setattr(post_agent, "publish_scheduled_post", lambda post, client: "external-id-123")

    posts_jobs.publish_due_posts(session_factory)

    with session_factory() as db:
        reloaded = db.get(Post, post_id)
        assert reloaded.status == PostStatus.published
        assert reloaded.published_at is not None

        from platform_core.models import ActivityEvent

        event = db.query(ActivityEvent).filter(ActivityEvent.entity_id == post_id).one()
        assert event.event_type == "published"
        assert event.details == {"triggered_by": "scheduled_job"}


def test_publish_due_posts_ignores_not_yet_due(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(session_factory, meta_page_id="page-1", meta_page_access_token="token-1")
    with session_factory() as db:
        post = Post(
            client_id=client,
            brief={},
            content={"caption": "Promo", "hashtags": []},
            status=PostStatus.scheduled,
            scheduled_at=datetime.now(UTC) + timedelta(days=1),
        )
        db.add(post)
        db.commit()
        post_id = post.id

    monkeypatch.setattr(
        post_agent, "publish_scheduled_post", lambda post, client: pytest.fail("ne doit pas être appelé")
    )

    posts_jobs.publish_due_posts(session_factory)

    with session_factory() as db:
        assert db.get(Post, post_id).status == PostStatus.scheduled


def test_publish_due_posts_failure_notifies_once(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(session_factory)
    with session_factory() as db:
        post = Post(
            client_id=client,
            brief={},
            content={"caption": "Promo", "hashtags": []},
            status=PostStatus.scheduled,
            scheduled_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        db.add(post)
        db.commit()
        post_id = post.id

    def _fail(post, client):
        raise post_agent.MissingMetaConnectionError("Page Meta non connectée")

    monkeypatch.setattr(post_agent, "publish_scheduled_post", _fail)

    posts_jobs.publish_due_posts(session_factory)
    posts_jobs.publish_due_posts(session_factory)

    with session_factory() as db:
        assert db.get(Post, post_id).status == PostStatus.scheduled
        notifications = db.query(Notification).filter(Notification.category == NotificationCategory.error_spike).all()
        assert len(notifications) == 1


# --- Maintenance : run_backups_and_retention ---------------------------------------------


def test_run_backups_skips_when_no_active_subscription(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(backup_module, "create_backup", lambda **kw: calls.append("create") or b"dump")

    maintenance_jobs.run_backups_and_retention(session_factory)

    assert calls == []


def test_run_backups_creates_backup_when_due(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_client(session_factory, pack=Pack.premium)
    monkeypatch.setattr(backup_module, "create_backup", lambda **kw: b"-- dump --")
    monkeypatch.setattr(backup_module, "upload_backup", lambda data, ts, **kw: "backups/fake.sql")
    retention_calls = []
    monkeypatch.setattr(backup_module, "apply_retention", lambda pack, **kw: retention_calls.append(pack))

    maintenance_jobs.run_backups_and_retention(session_factory)

    with session_factory() as db:
        from platform_core.models import Backup

        assert db.query(Backup).count() == 1
    assert retention_calls == [Pack.premium]


def test_run_backups_skips_when_within_interval(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_client(session_factory, pack=Pack.premium)
    with session_factory() as db:
        from platform_core.models import Backup

        db.add(Backup(r2_key="backups/recent.sql", size_bytes=1))
        db.commit()

    calls = []
    monkeypatch.setattr(backup_module, "create_backup", lambda **kw: calls.append("create") or b"dump")

    maintenance_jobs.run_backups_and_retention(session_factory)

    assert calls == []  # backup Premium (quotidien) déjà fait "maintenant" : pas dû.


def test_run_backups_failure_creates_critical_notification(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_client(session_factory, pack=Pack.starter)

    def _fail(**kwargs):
        raise RuntimeError("pg_dump introuvable")

    monkeypatch.setattr(backup_module, "create_backup", _fail)

    maintenance_jobs.run_backups_and_retention(session_factory)

    with session_factory() as db:
        notifications = db.query(Notification).filter(Notification.category == NotificationCategory.backup_failure).all()
        assert len(notifications) == 1


# --- Maintenance : run_security_scans -----------------------------------------------------


def test_run_security_scans_skipped_for_starter_only(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_client(session_factory, pack=Pack.starter)
    calls = []
    monkeypatch.setattr(security_scan_module, "run_pip_audit", lambda **kw: calls.append("scan") or [])

    maintenance_jobs.run_security_scans(session_factory)

    assert calls == []


def test_run_security_scans_creates_notification_with_no_findings(
    session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_client(session_factory, pack=Pack.business)
    monkeypatch.setattr(security_scan_module, "run_pip_audit", lambda **kw: [])

    maintenance_jobs.run_security_scans(session_factory)

    with session_factory() as db:
        notifications = (
            db.query(Notification).filter(Notification.category == NotificationCategory.security_finding).all()
        )
        assert len(notifications) == 1
        assert "aucune vulnérabilité" in notifications[0].message


def test_run_security_scans_reports_urgent_findings(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_client(session_factory, pack=Pack.premium)
    finding = security_scan_module.SecurityFinding(
        package="requests", installed_version="2.0.0", vulnerability_id="CVE-1234", severity="critical"
    )
    monkeypatch.setattr(security_scan_module, "run_pip_audit", lambda **kw: [finding])

    maintenance_jobs.run_security_scans(session_factory)

    with session_factory() as db:
        from platform_core.models import NotificationSeverity

        notifications = (
            db.query(Notification).filter(Notification.category == NotificationCategory.security_finding).all()
        )
        assert any(n.severity == NotificationSeverity.critical for n in notifications)


def test_run_security_scans_skips_when_within_interval(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_client(session_factory, pack=Pack.business)
    with session_factory() as db:
        from platform_core.models import NotificationSeverity

        db.add(
            Notification(
                category=NotificationCategory.security_finding,
                severity=NotificationSeverity.info,
                message="Scan précédent",
            )
        )
        db.commit()

    calls = []
    monkeypatch.setattr(security_scan_module, "run_pip_audit", lambda **kw: calls.append("scan") or [])

    maintenance_jobs.run_security_scans(session_factory)

    assert calls == []


# --- Maintenance : run_uptime_checks -------------------------------------------------------


def test_run_uptime_checks_ignores_sites_without_monitor(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(session_factory, pack=Pack.premium)
    with session_factory() as db:
        db.add(Site(client_id=client, sector="restaurant", brief={}, status=SiteStatus.published))
        db.commit()

    calls = []
    monkeypatch.setattr(uptime_module, "check_uptime", lambda monitor_id, **kw: calls.append(monitor_id))

    maintenance_jobs.run_uptime_checks(session_factory)

    assert calls == []


def test_run_uptime_checks_notifies_after_threshold(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(session_factory, pack=Pack.premium)
    with session_factory() as db:
        site = Site(
            client_id=client,
            sector="restaurant",
            brief={},
            status=SiteStatus.published,
            uptime_monitor_id="monitor-1",
            down_since=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=20),
        )
        db.add(site)
        db.commit()
        site_id = site.id

    monkeypatch.setattr(
        uptime_module, "check_uptime", lambda monitor_id, **kw: uptime_module.UptimeCheckResult(is_up=False, status_label="down")
    )

    maintenance_jobs.run_uptime_checks(session_factory)
    maintenance_jobs.run_uptime_checks(session_factory)  # ne doit pas dupliquer la notification

    with session_factory() as db:
        notifications = (
            db.query(Notification)
            .filter(Notification.site_id == site_id, Notification.category == NotificationCategory.site_down)
            .all()
        )
        assert len(notifications) == 1


def test_run_uptime_checks_resets_down_since_when_back_up(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(session_factory, pack=Pack.premium)
    with session_factory() as db:
        site = Site(
            client_id=client,
            sector="restaurant",
            brief={},
            status=SiteStatus.published,
            uptime_monitor_id="monitor-1",
            down_since=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=5),
        )
        db.add(site)
        db.commit()
        site_id = site.id

    monkeypatch.setattr(
        uptime_module, "check_uptime", lambda monitor_id, **kw: uptime_module.UptimeCheckResult(is_up=True, status_label="up")
    )

    maintenance_jobs.run_uptime_checks(session_factory)

    with session_factory() as db:
        assert db.get(Site, site_id).down_since is None


# --- Planning : send_appointment_reminders -------------------------------------------------


def _platform_whatsapp_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "platform_whatsapp_phone_number_id", "platform-number-id")
    monkeypatch.setattr(settings, "platform_whatsapp_access_token", "platform-token")


def test_send_appointment_reminders_noop_without_platform_credentials(
    session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "platform_whatsapp_phone_number_id", "")
    monkeypatch.setattr(settings, "platform_whatsapp_access_token", "")
    client = _make_client(session_factory, contact_phone="+24101020304")
    with session_factory() as db:
        db.add(
            Appointment(
                client_id=client,
                staff_contact="success@plateforme.example",
                purpose="Onboarding",
                scheduled_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=2),
                status=AppointmentStatus.confirmed,
            )
        )
        db.commit()

    calls = []
    monkeypatch.setattr(whatsapp_module, "send_whatsapp_message", lambda *a, **kw: calls.append(a) or "msg-id")

    planning_jobs.send_appointment_reminders(session_factory)

    assert calls == []


def test_send_appointment_reminders_sends_and_marks_sent(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _platform_whatsapp_configured(monkeypatch)
    client = _make_client(session_factory, contact_phone="+24101020304")
    with session_factory() as db:
        appointment = Appointment(
            client_id=client,
            staff_contact="success@plateforme.example",
            purpose="Onboarding",
            scheduled_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=2),
            status=AppointmentStatus.confirmed,
        )
        db.add(appointment)
        db.commit()
        appointment_id = appointment.id

    calls = []
    monkeypatch.setattr(
        whatsapp_module, "send_whatsapp_message", lambda *a, **kw: calls.append(a) or "msg-id"
    )

    planning_jobs.send_appointment_reminders(session_factory)

    assert len(calls) == 1
    phone_number_id, access_token, to, message = calls[0]
    assert phone_number_id == "platform-number-id"
    assert access_token == "platform-token"
    assert to == "+24101020304"
    assert "Onboarding" in message

    with session_factory() as db:
        assert db.get(Appointment, appointment_id).reminder_sent_at is not None


def test_send_appointment_reminders_does_not_duplicate(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _platform_whatsapp_configured(monkeypatch)
    client = _make_client(session_factory, contact_phone="+24101020304")
    with session_factory() as db:
        db.add(
            Appointment(
                client_id=client,
                staff_contact="success@plateforme.example",
                purpose="Onboarding",
                scheduled_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=2),
                status=AppointmentStatus.confirmed,
            )
        )
        db.commit()

    calls = []
    monkeypatch.setattr(whatsapp_module, "send_whatsapp_message", lambda *a, **kw: calls.append(a) or "msg-id")

    planning_jobs.send_appointment_reminders(session_factory)
    planning_jobs.send_appointment_reminders(session_factory)

    assert len(calls) == 1


def test_send_appointment_reminders_skips_without_contact_phone(
    session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    _platform_whatsapp_configured(monkeypatch)
    client = _make_client(session_factory)  # pas de contact_phone
    with session_factory() as db:
        db.add(
            Appointment(
                client_id=client,
                staff_contact="success@plateforme.example",
                purpose="Onboarding",
                scheduled_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=2),
                status=AppointmentStatus.confirmed,
            )
        )
        db.commit()

    calls = []
    monkeypatch.setattr(whatsapp_module, "send_whatsapp_message", lambda *a, **kw: calls.append(a) or "msg-id")

    planning_jobs.send_appointment_reminders(session_factory)

    assert calls == []


def test_send_appointment_reminders_skips_outside_window(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _platform_whatsapp_configured(monkeypatch)
    client = _make_client(session_factory, contact_phone="+24101020304")
    with session_factory() as db:
        db.add(
            Appointment(
                client_id=client,
                staff_contact="success@plateforme.example",
                purpose="Onboarding",
                scheduled_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=5),
                status=AppointmentStatus.confirmed,
            )
        )
        db.commit()

    calls = []
    monkeypatch.setattr(whatsapp_module, "send_whatsapp_message", lambda *a, **kw: calls.append(a) or "msg-id")

    planning_jobs.send_appointment_reminders(session_factory)

    assert calls == []


def test_send_appointment_reminders_failure_notifies_once(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _platform_whatsapp_configured(monkeypatch)
    client = _make_client(session_factory, contact_phone="+24101020304")
    with session_factory() as db:
        appointment = Appointment(
            client_id=client,
            staff_contact="success@plateforme.example",
            purpose="Onboarding",
            scheduled_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=2),
            status=AppointmentStatus.confirmed,
        )
        db.add(appointment)
        db.commit()
        appointment_id = appointment.id

    def _fail(*a, **kw):
        raise whatsapp_module.WhatsAppSendError("échec API WhatsApp")

    monkeypatch.setattr(whatsapp_module, "send_whatsapp_message", _fail)

    planning_jobs.send_appointment_reminders(session_factory)
    planning_jobs.send_appointment_reminders(session_factory)

    with session_factory() as db:
        assert db.get(Appointment, appointment_id).reminder_sent_at is None
        notifications = (
            db.query(Notification).filter(Notification.category == NotificationCategory.error_spike).all()
        )
        assert len(notifications) == 1
