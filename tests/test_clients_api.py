from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
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


def test_create_client_returns_id_and_api_key(db_session: Session) -> None:
    client = TestClient(app)

    resp = client.post("/api/clients", json={"name": "Chez Awa", "sector": "restaurant"})

    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert len(body["api_key"]) > 20


def test_created_api_key_authenticates_subsequent_requests(db_session: Session) -> None:
    client = TestClient(app)

    create_resp = client.post("/api/clients", json={"name": "Chez Awa", "sector": "restaurant"})
    api_key = create_resp.json()["api_key"]

    site_resp = client.post(
        "/api/sites",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "business_name": "Chez Awa",
            "sector": "restaurant",
            "description": "Restaurant familial",
            "phone": "+24101020304",
        },
    )
    assert site_resp.status_code == 201
