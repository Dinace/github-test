import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from platform_core.activity import log_event
from platform_core.auth import create_client_with_api_key
from platform_core.db import Base
from platform_core.models import ActivityEvent


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


def test_log_event_persists_and_is_queryable(db_session: Session, client_id: uuid.UUID) -> None:
    entity_id = uuid.uuid4()

    log_event(
        db_session,
        client_id=client_id,
        agent="prospection",
        entity_type="prospect",
        entity_id=entity_id,
        event_type="created",
        details={"category": "favorable"},
    )

    events = db_session.query(ActivityEvent).filter(ActivityEvent.entity_id == entity_id).all()
    assert len(events) == 1
    assert events[0].agent == "prospection"
    assert events[0].details == {"category": "favorable"}
