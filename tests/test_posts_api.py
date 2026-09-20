import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.reseaux_sociaux import agent as post_agent
from agents.reseaux_sociaux import meta
from agents.reseaux_sociaux.content import PostContent
from app.main import app
from platform_core.auth import create_client_with_api_key
from platform_core.db import Base, get_db
from platform_core.models import ActivityEvent

_BRIEF_PAYLOAD = {
    "objective": "promotion",
    "mandatory_elements": ["Prix : 5000 FCFA"],
}


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


def _fake_content() -> PostContent:
    return PostContent(caption="Une belle promotion vous attend !", hashtags=["promo"])


def test_full_workflow_up_to_scheduling(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, auth_headers: dict[str, str]
) -> None:
    monkeypatch.setattr(post_agent, "generate_draft_content", lambda brief, brand_voice, **kw: _fake_content())

    client = TestClient(app)

    create_resp = client.post("/api/posts", headers=auth_headers, json=_BRIEF_PAYLOAD)
    assert create_resp.status_code == 201
    post_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "draft"

    generate_resp = client.post(f"/api/posts/{post_id}/generate", headers=auth_headers)
    assert generate_resp.status_code == 200
    assert generate_resp.json()["status"] == "pending_validation"

    # Le client demande une modification -> retour à brouillon, contenu réinitialisé.
    changes_resp = client.post(f"/api/posts/{post_id}/request-changes", headers=auth_headers)
    assert changes_resp.status_code == 200
    assert changes_resp.json()["status"] == "draft"

    # Deuxième génération, puis validation cette fois.
    client.post(f"/api/posts/{post_id}/generate", headers=auth_headers)
    validate_resp = client.post(f"/api/posts/{post_id}/validate", headers=auth_headers)
    assert validate_resp.status_code == 200
    assert validate_resp.json()["status"] == "validated"

    scheduled_at = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    schedule_resp = client.post(
        f"/api/posts/{post_id}/schedule", headers=auth_headers, json={"scheduled_at": scheduled_at}
    )
    assert schedule_resp.status_code == 200
    assert schedule_resp.json()["status"] == "scheduled"

    # Journalisé pour l'agent Planning (platform_core.activity.log_event) — comble le point
    # ouvert "Réseaux sociaux n'émet pas encore d'événements".
    event_types = [
        e.event_type
        for e in db_session.query(ActivityEvent)
        .filter(ActivityEvent.entity_id == uuid.UUID(post_id))
        .order_by(ActivityEvent.occurred_at)
        .all()
    ]
    assert event_types == [
        "created",
        "content_generated",
        "changes_requested",
        "content_generated",
        "validated",
        "scheduled",
    ]


def test_publish_requires_meta_connection(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, auth_headers: dict[str, str]
) -> None:
    monkeypatch.setattr(post_agent, "generate_draft_content", lambda brief, brand_voice, **kw: _fake_content())

    client = TestClient(app)
    post_id = client.post("/api/posts", headers=auth_headers, json=_BRIEF_PAYLOAD).json()["id"]
    client.post(f"/api/posts/{post_id}/generate", headers=auth_headers)
    client.post(f"/api/posts/{post_id}/validate", headers=auth_headers)
    scheduled_at = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    schedule_resp = client.post(
        f"/api/posts/{post_id}/schedule", headers=auth_headers, json={"scheduled_at": scheduled_at}
    )
    assert schedule_resp.status_code == 200

    # Le client de test n'a pas de meta_page_id/meta_page_access_token renseignés.
    publish_resp = client.post(f"/api/posts/{post_id}/publish", headers=auth_headers)
    assert publish_resp.status_code == 412


def test_publish_succeeds_once_meta_is_connected(
    monkeypatch: pytest.MonkeyPatch, db_session: Session, auth_headers: dict[str, str]
) -> None:
    monkeypatch.setattr(post_agent, "generate_draft_content", lambda brief, brand_voice, **kw: _fake_content())
    monkeypatch.setattr(meta, "publish_to_meta", lambda page_id, token, message, **kw: "fake-post-id")

    from platform_core.models import Client

    test_client = db_session.query(Client).first()
    test_client.meta_page_id = "123456"
    test_client.meta_page_access_token = "fake-token"
    db_session.commit()

    client = TestClient(app)
    post_id = client.post("/api/posts", headers=auth_headers, json=_BRIEF_PAYLOAD).json()["id"]
    client.post(f"/api/posts/{post_id}/generate", headers=auth_headers)
    client.post(f"/api/posts/{post_id}/validate", headers=auth_headers)
    scheduled_at = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    schedule_resp = client.post(
        f"/api/posts/{post_id}/schedule", headers=auth_headers, json={"scheduled_at": scheduled_at}
    )
    assert schedule_resp.status_code == 200

    publish_resp = client.post(f"/api/posts/{post_id}/publish", headers=auth_headers)
    assert publish_resp.status_code == 200
    assert publish_resp.json()["status"] == "published"

    last_event = (
        db_session.query(ActivityEvent)
        .filter(ActivityEvent.entity_id == uuid.UUID(post_id))
        .order_by(ActivityEvent.occurred_at.desc())
        .first()
    )
    assert last_event.event_type == "published"


def test_cannot_validate_a_post_still_in_draft(db_session: Session, auth_headers: dict[str, str]) -> None:
    client = TestClient(app)
    post_id = client.post("/api/posts", headers=auth_headers, json=_BRIEF_PAYLOAD).json()["id"]

    resp = client.post(f"/api/posts/{post_id}/validate", headers=auth_headers)
    assert resp.status_code == 409


def test_client_cannot_access_another_clients_post(db_session: Session, auth_headers: dict[str, str]) -> None:
    client = TestClient(app)
    post_id = client.post("/api/posts", headers=auth_headers, json=_BRIEF_PAYLOAD).json()["id"]

    _other_client, other_api_key = create_client_with_api_key(db_session, name="Autre PME", sector="boutique")
    other_headers = {"Authorization": f"Bearer {other_api_key}"}

    resp = client.post(f"/api/posts/{post_id}/generate", headers=other_headers)
    assert resp.status_code == 403
