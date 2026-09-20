import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from platform_core.auth import create_client_with_api_key
from platform_core.config import settings
from platform_core.db import Base, get_db


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


@pytest.fixture()
def client_and_headers(db_session: Session) -> tuple[uuid.UUID, dict[str, str]]:
    client, api_key = create_client_with_api_key(db_session, name="Chez Awa", sector="restaurant")
    return client.id, {"Authorization": f"Bearer {api_key}"}


def test_staff_endpoints_require_ops_token(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ops_api_token", "test-ops-token")
    client = TestClient(app)

    resp = client.get(f"/api/planning/clients/{uuid.uuid4()}/summary")
    assert resp.status_code == 401


def test_staff_can_view_client_summary(
    db_session: Session, ops_headers: dict[str, str], client_and_headers: tuple[uuid.UUID, dict[str, str]]
) -> None:
    client_id, _ = client_and_headers
    client = TestClient(app)

    resp = client.get(f"/api/planning/clients/{client_id}/summary", headers=ops_headers)

    assert resp.status_code == 200
    assert resp.json()["sites_awaiting_validation"] == 0


def test_staff_digest_uses_claude(
    monkeypatch: pytest.MonkeyPatch,
    db_session: Session,
    ops_headers: dict[str, str],
    client_and_headers: tuple[uuid.UUID, dict[str, str]],
) -> None:
    monkeypatch.setattr(
        "app.routers.planning.generate_digest", lambda summary, **kw: "Tout est calme pour ce client."
    )
    client_id, _ = client_and_headers
    client = TestClient(app)

    resp = client.get(f"/api/planning/clients/{client_id}/digest", headers=ops_headers)

    assert resp.status_code == 200
    assert resp.json()["digest"] == "Tout est calme pour ce client."


def test_staff_propose_list_and_complete_appointment(
    db_session: Session, ops_headers: dict[str, str], client_and_headers: tuple[uuid.UUID, dict[str, str]]
) -> None:
    client_id, _ = client_and_headers
    scheduled_at = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    client = TestClient(app)

    propose_resp = client.post(
        "/api/planning/appointments",
        headers=ops_headers,
        json={
            "client_id": str(client_id),
            "staff_contact": "success@plateforme.example",
            "purpose": "Onboarding",
            "scheduled_at": scheduled_at,
            "duration_minutes": 45,
        },
    )
    assert propose_resp.status_code == 201
    appointment_id = propose_resp.json()["id"]
    assert propose_resp.json()["status"] == "proposed"

    list_resp = client.get("/api/planning/appointments", headers=ops_headers)
    assert len(list_resp.json()) == 1

    complete_resp = client.post(
        f"/api/planning/appointments/{appointment_id}/complete",
        headers=ops_headers,
        json={"notes": "RDV effectué, client satisfait"},
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"


def test_client_can_view_and_confirm_own_appointment(
    db_session: Session, ops_headers: dict[str, str], client_and_headers: tuple[uuid.UUID, dict[str, str]]
) -> None:
    client_id, client_headers = client_and_headers
    scheduled_at = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    client = TestClient(app)

    propose_resp = client.post(
        "/api/planning/appointments",
        headers=ops_headers,
        json={
            "client_id": str(client_id),
            "staff_contact": "success@plateforme.example",
            "purpose": "Onboarding",
            "scheduled_at": scheduled_at,
        },
    )
    appointment_id = propose_resp.json()["id"]

    my_appointments = client.get("/api/planning/me/appointments", headers=client_headers)
    assert len(my_appointments.json()) == 1

    confirm_resp = client.post(f"/api/planning/me/appointments/{appointment_id}/confirm", headers=client_headers)
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "confirmed"


def test_client_cannot_confirm_another_clients_appointment(
    db_session: Session, ops_headers: dict[str, str], client_and_headers: tuple[uuid.UUID, dict[str, str]]
) -> None:
    client_id, _ = client_and_headers
    scheduled_at = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    client = TestClient(app)

    propose_resp = client.post(
        "/api/planning/appointments",
        headers=ops_headers,
        json={
            "client_id": str(client_id),
            "staff_contact": "success@plateforme.example",
            "purpose": "Onboarding",
            "scheduled_at": scheduled_at,
        },
    )
    appointment_id = propose_resp.json()["id"]

    _other_client, other_api_key = create_client_with_api_key(db_session, name="Autre PME", sector="boutique")
    other_headers = {"Authorization": f"Bearer {other_api_key}"}

    resp = client.post(f"/api/planning/me/appointments/{appointment_id}/confirm", headers=other_headers)
    assert resp.status_code == 403
