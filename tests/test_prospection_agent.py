import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.prospection.agent import search_and_score
from platform_core.auth import create_client_with_api_key
from platform_core.db import Base
from platform_core.models import ProspectCategory


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


class _FakeHttpClient:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def post(self, url: str, *, json: dict, headers: dict) -> _FakeResponse:
        return _FakeResponse(self._payload)


@pytest.fixture()
def db_session(tmp_path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


@pytest.fixture()
def client_id(db_session: Session) -> uuid.UUID:
    client, _api_key = create_client_with_api_key(db_session, name="Chez Awa", sector="restaurant")
    return client.id


def test_search_and_score_creates_prospects_with_categories(db_session: Session, client_id: uuid.UUID) -> None:
    payload = {
        "places": [
            {
                "displayName": {"text": "Restaurant Sans Site"},
                "nationalPhoneNumber": "+24101020304",
                "rating": 4.8,
                "userRatingCount": 30,
            },
            {"displayName": {"text": "Restaurant Sans Contact"}},
        ]
    }
    fake_http = _FakeHttpClient(payload)

    prospects = search_and_score(client_id, "restaurant Libreville", "restaurant", db=db_session, http_client=fake_http)

    assert len(prospects) == 2
    favorable = next(p for p in prospects if p.business_name == "Restaurant Sans Site")
    unreachable = next(p for p in prospects if p.business_name == "Restaurant Sans Contact")

    assert favorable.category == ProspectCategory.favorable
    assert unreachable.category == ProspectCategory.non_joignable
    assert all(p.client_id == client_id for p in prospects)
    assert all(p.source == "google_places" for p in prospects)
