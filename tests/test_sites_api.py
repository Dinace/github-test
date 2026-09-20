import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.creation_site import agent as site_agent
from agents.creation_site.content import ContentItem, SiteContent
from app.main import app
from platform_core.db import Base, get_db
from platform_core.models import Client


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
def client_id(db_session: Session) -> uuid.UUID:
    client = Client(name="Chez Awa", sector="restaurant")
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client.id


def test_create_generate_preview_publish_flow(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, client_id: uuid.UUID
) -> None:
    fake_content = SiteContent(
        hero_tagline="Bienvenue",
        hero_subtitle="Sous-titre",
        about_text="À propos.",
        items=[ContentItem(title="Item", description="Description")],
        contact_intro="Contactez-nous",
    )

    def fake_generate_draft_site(site_id, brief, *, client=None) -> SiteContent:
        return fake_content

    # Patché sur le module utilisé par le routeur (app.routers.sites importe le module
    # `agent`, pas la fonction directement), pour que le patch soit bien pris en compte.
    monkeypatch.setattr(site_agent, "generate_draft_site", fake_generate_draft_site)

    client = TestClient(app)

    create_resp = client.post(
        "/api/sites",
        params={"client_id": str(client_id)},
        json={
            "business_name": "Chez Awa",
            "sector": "restaurant",
            "description": "Restaurant familial",
            "phone": "+24101020304",
        },
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["status"] == "draft"
    site_id = body["id"]

    generate_resp = client.post(f"/api/sites/{site_id}/generate")
    assert generate_resp.status_code == 200

    preview_resp = client.get(f"/api/sites/{site_id}/preview")
    assert preview_resp.status_code == 200
    assert "Chez Awa" in preview_resp.text
    assert "Bienvenue" in preview_resp.text

    publish_resp = client.post(f"/api/sites/{site_id}/publish")
    assert publish_resp.status_code == 200
    assert publish_resp.json()["status"] == "published"


def test_preview_before_generation_returns_conflict(db_session: Session, client_id: uuid.UUID) -> None:
    client = TestClient(app)

    create_resp = client.post(
        "/api/sites",
        params={"client_id": str(client_id)},
        json={
            "business_name": "Chez Awa",
            "sector": "restaurant",
            "description": "Restaurant familial",
            "phone": "+24101020304",
        },
    )
    site_id = create_resp.json()["id"]

    preview_resp = client.get(f"/api/sites/{site_id}/preview")
    assert preview_resp.status_code == 409
