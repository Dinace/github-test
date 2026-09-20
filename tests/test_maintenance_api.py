from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.maintenance import backup as backup_module
from app.main import app
from platform_core.config import settings
from platform_core.db import Base, get_db
from platform_core.models import Backup, Notification, NotificationCategory, NotificationSeverity


@pytest.fixture()
def db_session(tmp_path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    testing_session_local = sessionmaker(bind=engine)

    def override_get_db() -> Iterator[Session]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    session = testing_session_local()
    yield session
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture()
def ops_headers(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    monkeypatch.setattr(settings, "ops_api_token", "test-ops-token")
    return {"Authorization": "Bearer test-ops-token"}


def test_maintenance_endpoints_require_ops_token(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ops_api_token", "test-ops-token")
    client = TestClient(app)

    resp = client.get("/api/maintenance/notifications")
    assert resp.status_code == 401


def test_maintenance_endpoints_503_when_ops_token_unconfigured(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "ops_api_token", "")
    client = TestClient(app)

    resp = client.get(
        "/api/maintenance/notifications", headers={"Authorization": "Bearer anything"}
    )
    assert resp.status_code == 503


def test_list_and_acknowledge_notifications(db_session: Session, ops_headers: dict[str, str]) -> None:
    notification = Notification(
        category=NotificationCategory.site_down,
        severity=NotificationSeverity.critical,
        message="Le site de Chez Awa est injoignable depuis 20 minutes",
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    client = TestClient(app)

    list_resp = client.get("/api/maintenance/notifications", headers=ops_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    ack_resp = client.post(
        f"/api/maintenance/notifications/{notification.id}/acknowledge",
        headers=ops_headers,
        json={"acknowledged_by": "ops@example.com"},
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "acknowledged"

    # Une fois acquittée, elle ne doit plus apparaître dans la liste des "pending".
    list_after = client.get("/api/maintenance/notifications", headers=ops_headers)
    assert list_after.json() == []


def test_trigger_backup_creates_record(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, ops_headers: dict[str, str]
) -> None:
    monkeypatch.setattr(backup_module, "create_backup", lambda **kw: b"-- dump --")
    monkeypatch.setattr(backup_module, "upload_backup", lambda data, ts, **kw: "backups/fake-key.sql")

    client = TestClient(app)
    resp = client.post("/api/maintenance/backups", headers=ops_headers)

    assert resp.status_code == 201
    assert resp.json()["r2_key"] == "backups/fake-key.sql"

    list_resp = client.get("/api/maintenance/backups", headers=ops_headers)
    assert len(list_resp.json()) == 1


def test_trigger_backup_failure_creates_critical_notification(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, ops_headers: dict[str, str]
) -> None:
    def failing_create_backup(**kwargs):
        raise RuntimeError("pg_dump introuvable")

    monkeypatch.setattr(backup_module, "create_backup", failing_create_backup)

    client = TestClient(app)
    resp = client.post("/api/maintenance/backups", headers=ops_headers)

    assert resp.status_code == 502
    notifications = client.get("/api/maintenance/notifications", headers=ops_headers).json()
    assert len(notifications) == 1
    assert notifications[0]["category"] == "backup_failure"
    assert notifications[0]["severity"] == "critical"


def test_restore_workflow_end_to_end_via_api(db_session: Session, ops_headers: dict[str, str]) -> None:
    backup = Backup(r2_key="backups/20260101T000000Z.sql", size_bytes=10)
    db_session.add(backup)
    db_session.commit()
    db_session.refresh(backup)

    client = TestClient(app)

    propose_resp = client.post(
        f"/api/maintenance/backups/{backup.id}/restore-requests",
        headers=ops_headers,
        json={"reason": "Corruption de données suite à un déploiement"},
    )
    assert propose_resp.status_code == 201
    restore_id = propose_resp.json()["id"]
    assert propose_resp.json()["status"] == "proposed"

    # Exécuter avant confirmation doit être refusé (409), jamais silencieusement autorisé.
    premature_execute = client.post(
        f"/api/maintenance/restore-requests/{restore_id}/execute", headers=ops_headers
    )
    assert premature_execute.status_code == 409

    confirm_resp = client.post(
        f"/api/maintenance/restore-requests/{restore_id}/confirm",
        headers=ops_headers,
        json={"confirmed_by": "admin@example.com"},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "confirmed"


def test_sentry_webhook_creates_notification_without_ops_token(db_session: Session) -> None:
    client = TestClient(app)

    resp = client.post(
        "/api/maintenance/webhooks/sentry",
        json={"data": {"event": {"message": "TypeError dans generate_content", "level": "error"}}},
    )

    assert resp.status_code == 202
