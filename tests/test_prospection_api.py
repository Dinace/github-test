import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.prospection import agent as prospection_agent
from agents.prospection import whatsapp
from agents.prospection.content import ContactMessage
from app.main import app
from platform_core.auth import create_client_with_api_key
from platform_core.db import Base, get_db
from platform_core.models import Client, ContactStatus, Prospect, ProspectCategory


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
def auth_headers(db_session: Session) -> dict[str, str]:
    _client, api_key = create_client_with_api_key(db_session, name="Chez Awa", sector="restaurant")
    return {"Authorization": f"Bearer {api_key}"}


def _make_prospect(db: Session, client_id: uuid.UUID, category: ProspectCategory, phone: str | None = "+24101020304") -> Prospect:
    prospect = Prospect(
        client_id=client_id,
        business_name="Boutique Test",
        sector="boutique",
        phone=phone,
        source="google_places",
        raw_data={"website_uri": None},
        category=category,
        score=5,
    )
    db.add(prospect)
    db.commit()
    db.refresh(prospect)
    return prospect


def test_search_creates_and_returns_prospects(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, auth_headers: dict[str, str]
) -> None:
    def fake_search_and_score(client_id, query, sector, *, db, http_client=None):
        return [_make_prospect(db, client_id, ProspectCategory.favorable)]

    monkeypatch.setattr(prospection_agent, "search_and_score", fake_search_and_score)

    client = TestClient(app)
    resp = client.post("/api/prospects/search", headers=auth_headers, json={"query": "boutique", "sector": "boutique"})

    assert resp.status_code == 201
    assert resp.json()[0]["category"] == "favorable"


def test_propose_contact_blocked_for_non_favorable(db_session: Session, auth_headers: dict[str, str]) -> None:
    client_row = db_session.query(Client).first()
    prospect = _make_prospect(db_session, client_row.id, ProspectCategory.non_favorable)

    client = TestClient(app)
    resp = client.post(f"/api/prospects/{prospect.id}/propose-contact", headers=auth_headers)

    assert resp.status_code == 403


def test_propose_contact_blocked_for_non_joignable(db_session: Session, auth_headers: dict[str, str]) -> None:
    client_row = db_session.query(Client).first()
    prospect = _make_prospect(db_session, client_row.id, ProspectCategory.non_joignable, phone=None)

    client = TestClient(app)
    resp = client.post(f"/api/prospects/{prospect.id}/propose-contact", headers=auth_headers)

    assert resp.status_code == 403


def test_full_contact_workflow_for_favorable_prospect(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, auth_headers: dict[str, str]
) -> None:
    monkeypatch.setattr(
        "app.routers.prospection.generate_contact_message",
        lambda *a, **kw: ContactMessage(message="Bonjour, nous pouvons vous aider !"),
    )
    monkeypatch.setattr(whatsapp, "send_whatsapp_message", lambda *a, **kw: "wamid.fake")

    client_row = db_session.query(Client).first()
    client_row.whatsapp_phone_number_id = "1234567890"
    client_row.whatsapp_access_token = "fake-token"
    db_session.commit()

    prospect = _make_prospect(db_session, client_row.id, ProspectCategory.favorable)

    client = TestClient(app)

    propose_resp = client.post(f"/api/prospects/{prospect.id}/propose-contact", headers=auth_headers)
    assert propose_resp.status_code == 200
    assert propose_resp.json()["contact_status"] == "pending_validation"

    validate_resp = client.post(f"/api/prospects/{prospect.id}/validate-contact", headers=auth_headers)
    assert validate_resp.status_code == 200
    assert validate_resp.json()["contact_status"] == "validated"

    send_resp = client.post(f"/api/prospects/{prospect.id}/send-contact", headers=auth_headers)
    assert send_resp.status_code == 200
    assert send_resp.json()["contact_status"] == "sent"


def test_send_contact_requires_whatsapp_connection(db_session: Session, auth_headers: dict[str, str]) -> None:
    client_row = db_session.query(Client).first()
    prospect = _make_prospect(db_session, client_row.id, ProspectCategory.favorable)
    prospect.contact_status = ContactStatus.validated
    prospect.contact_message = {"message": "Bonjour"}
    db_session.commit()

    client = TestClient(app)
    resp = client.post(f"/api/prospects/{prospect.id}/send-contact", headers=auth_headers)

    assert resp.status_code == 412


def test_get_offer_returns_pdf(db_session: Session, auth_headers: dict[str, str]) -> None:
    client_row = db_session.query(Client).first()
    prospect = _make_prospect(db_session, client_row.id, ProspectCategory.favorable)

    client = TestClient(app)
    resp = client.get(f"/api/prospects/{prospect.id}/offer", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_client_cannot_access_another_clients_prospect(db_session: Session, auth_headers: dict[str, str]) -> None:
    client_row = db_session.query(Client).first()
    prospect = _make_prospect(db_session, client_row.id, ProspectCategory.favorable)

    _other_client, other_api_key = create_client_with_api_key(db_session, name="Autre PME", sector="boutique")
    other_headers = {"Authorization": f"Bearer {other_api_key}"}

    client = TestClient(app)
    resp = client.get(f"/api/prospects/{prospect.id}/offer", headers=other_headers)

    assert resp.status_code == 403
