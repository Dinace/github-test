import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.creation_site import agent as site_agent
from agents.creation_site import storage
from agents.creation_site.content import ContentItem, SiteContent
from app.main import app
from platform_core.auth import create_client_with_api_key
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
def auth_headers(db_session: Session) -> dict[str, str]:
    _client, api_key = create_client_with_api_key(db_session, name="Chez Awa", sector="restaurant")
    return {"Authorization": f"Bearer {api_key}"}


_BRIEF_PAYLOAD = {
    "business_name": "Chez Awa",
    "sector": "restaurant",
    "description": "Restaurant familial",
    "phone": "+24101020304",
}


def _fake_content() -> SiteContent:
    return SiteContent(
        hero_tagline="Bienvenue",
        hero_subtitle="Sous-titre",
        about_text="À propos.",
        items=[ContentItem(title="Item", description="Description")],
        contact_intro="Contactez-nous",
    )


def test_create_generate_preview_publish_flow(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, auth_headers: dict[str, str]
) -> None:
    monkeypatch.setattr(
        site_agent, "generate_draft_site", lambda site_id, brief, **kwargs: _fake_content()
    )
    monkeypatch.setattr(storage, "promote_to_live", lambda site_id, **kwargs: [])

    client = TestClient(app)

    create_resp = client.post("/api/sites", headers=auth_headers, json=_BRIEF_PAYLOAD)
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["status"] == "draft"
    site_id = body["id"]

    generate_resp = client.post(f"/api/sites/{site_id}/generate", headers=auth_headers)
    assert generate_resp.status_code == 200

    preview_resp = client.get(f"/api/sites/{site_id}/preview", headers=auth_headers)
    assert preview_resp.status_code == 200
    assert "Chez Awa" in preview_resp.text
    assert "Bienvenue" in preview_resp.text

    publish_resp = client.post(f"/api/sites/{site_id}/publish", headers=auth_headers)
    assert publish_resp.status_code == 200
    assert publish_resp.json()["status"] == "published"


def test_preview_before_generation_returns_conflict(
    db_session: Session, auth_headers: dict[str, str]
) -> None:
    client = TestClient(app)

    create_resp = client.post("/api/sites", headers=auth_headers, json=_BRIEF_PAYLOAD)
    site_id = create_resp.json()["id"]

    preview_resp = client.get(f"/api/sites/{site_id}/preview", headers=auth_headers)
    assert preview_resp.status_code == 409


def test_requests_without_api_key_are_rejected(db_session: Session) -> None:
    client = TestClient(app)

    resp = client.post("/api/sites", json=_BRIEF_PAYLOAD)
    assert resp.status_code == 401


def test_requests_with_wrong_api_key_are_rejected(db_session: Session, auth_headers: dict[str, str]) -> None:
    client = TestClient(app)

    resp = client.post("/api/sites", headers={"Authorization": "Bearer not-a-real-key"}, json=_BRIEF_PAYLOAD)
    assert resp.status_code == 401


def test_client_cannot_access_another_clients_site(db_session: Session, auth_headers: dict[str, str]) -> None:
    client = TestClient(app)

    create_resp = client.post("/api/sites", headers=auth_headers, json=_BRIEF_PAYLOAD)
    site_id = create_resp.json()["id"]

    _other_client, other_api_key = create_client_with_api_key(db_session, name="Autre PME", sector="boutique")
    other_headers = {"Authorization": f"Bearer {other_api_key}"}

    resp = client.get(f"/api/sites/{site_id}/preview", headers=other_headers)
    assert resp.status_code == 403
