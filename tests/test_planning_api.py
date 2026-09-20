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
from platform_core.models import Site, SiteStatus, Subscription


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


def test_staff_can_view_client_onboarding_checklist(
    db_session: Session, ops_headers: dict[str, str], client_and_headers: tuple[uuid.UUID, dict[str, str]]
) -> None:
    client_id, _ = client_and_headers
    db_session.add(Site(client_id=client_id, sector="restaurant", brief={}, status=SiteStatus.draft))
    db_session.commit()
    client = TestClient(app)

    resp = client.get(f"/api/planning/clients/{client_id}/onboarding", headers=ops_headers)

    assert resp.status_code == 200
    steps = {s["key"]: s["done"] for s in resp.json()}
    assert steps["site_created"] is True
    assert steps["site_published"] is False


def test_staff_can_view_and_update_client_project_info(
    db_session: Session, ops_headers: dict[str, str], client_and_headers: tuple[uuid.UUID, dict[str, str]]
) -> None:
    client_id, _ = client_and_headers
    client = TestClient(app)

    info_resp = client.get(f"/api/planning/clients/{client_id}/project-info", headers=ops_headers)
    assert info_resp.status_code == 200
    assert info_resp.json()["business_name"] == "Chez Awa"
    assert info_resp.json()["meta_connected"] is False
    assert info_resp.json()["project_notes"] is None

    notes_resp = client.put(
        f"/api/planning/clients/{client_id}/notes",
        headers=ops_headers,
        json={"notes": "Préfère être recontacté après 17h."},
    )
    assert notes_resp.status_code == 200
    assert notes_resp.json()["project_notes"] == "Préfère être recontacté après 17h."


def test_staff_can_set_client_network_access_without_leaking_secrets_back(
    db_session: Session, ops_headers: dict[str, str], client_and_headers: tuple[uuid.UUID, dict[str, str]]
) -> None:
    client_id, _ = client_and_headers
    client = TestClient(app)

    resp = client.put(
        f"/api/planning/clients/{client_id}/network-access",
        headers=ops_headers,
        json={"meta_page_id": "123456", "meta_page_access_token": "super-secret-token"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["meta_connected"] is True
    assert body["whatsapp_connected"] is False
    # La réponse ne doit jamais contenir la valeur du token soumis, seulement l'indicateur.
    assert "super-secret-token" not in resp.text
    assert "meta_page_access_token" not in body

    # La checklist "office manager" reflète bien le nouvel accès.
    onboarding_resp = client.get(f"/api/planning/clients/{client_id}/onboarding", headers=ops_headers)
    steps = {s["key"]: s["done"] for s in onboarding_resp.json()}
    assert "meta_page_connected" not in steps  # Starter par défaut, pas de pack Business/Premium


def test_network_access_endpoint_requires_ops_token(
    db_session: Session, monkeypatch: pytest.MonkeyPatch, client_and_headers: tuple[uuid.UUID, dict[str, str]]
) -> None:
    monkeypatch.setattr(settings, "ops_api_token", "test-ops-token")
    client_id, _ = client_and_headers
    client = TestClient(app)

    resp = client.put(
        f"/api/planning/clients/{client_id}/network-access",
        json={"meta_page_access_token": "secret"},
    )

    assert resp.status_code == 401


def test_client_can_view_own_onboarding_checklist(
    db_session: Session, client_and_headers: tuple[uuid.UUID, dict[str, str]]
) -> None:
    _client_id, client_headers = client_and_headers
    client = TestClient(app)

    resp = client.get("/api/planning/me/onboarding", headers=client_headers)

    assert resp.status_code == 200
    assert any(s["key"] == "site_created" for s in resp.json())


def test_staff_can_list_and_acknowledge_onboarding_notifications_by_team(
    db_session: Session, ops_headers: dict[str, str], client_and_headers: tuple[uuid.UUID, dict[str, str]]
) -> None:
    client_id, _ = client_and_headers
    db_session.add(Subscription(client_id=client_id, pack="business", price_amount=1000, payment_provider="orange_money"))
    db_session.add(Site(client_id=client_id, sector="restaurant", brief={}, status=SiteStatus.published, content={"x": 1}))
    db_session.commit()

    client = TestClient(app)

    from sqlalchemy.orm import sessionmaker

    from agents.planning.scheduled_jobs import notify_onboarding_progress

    # Appelé directement (pas via le scheduler, jamais démarré pendant les tests), avec un
    # sessionmaker séparé sur le même moteur que db_session, pour créer les notifications à
    # vérifier ci-dessous sans entrelacer le cycle de vie de la session de la fixture.
    notify_onboarding_progress(sessionmaker(bind=db_session.get_bind()))

    commercial_resp = client.get("/api/planning/notifications", headers=ops_headers, params={"team": "commercial"})
    assert commercial_resp.status_code == 200
    assert len(commercial_resp.json()) >= 1
    notification_id = commercial_resp.json()[0]["id"]

    technique_resp = client.get("/api/planning/notifications", headers=ops_headers, params={"team": "technique"})
    assert all(n["team"] == "technique" for n in technique_resp.json())

    ack_resp = client.post(
        f"/api/planning/notifications/{notification_id}/acknowledge",
        headers=ops_headers,
        json={"acknowledged_by": "commercial@plateforme.example"},
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "acknowledged"

    # Une fois acquittée, elle ne doit plus apparaître dans la liste "pending".
    after = client.get("/api/planning/notifications", headers=ops_headers, params={"team": "commercial"})
    assert notification_id not in [n["id"] for n in after.json()]


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
