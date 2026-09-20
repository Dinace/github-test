import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.planning.pipeline import get_prospect_pipeline
from platform_core.activity import log_event
from platform_core.auth import create_client_with_api_key
from platform_core.db import Base


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


def test_pipeline_returns_events_in_chronological_order(db_session: Session, client_id: uuid.UUID) -> None:
    prospect_id = uuid.uuid4()
    other_prospect_id = uuid.uuid4()

    log_event(
        db_session, client_id=client_id, agent="prospection", entity_type="prospect",
        entity_id=prospect_id, event_type="created",
    )
    log_event(
        db_session, client_id=client_id, agent="prospection", entity_type="prospect",
        entity_id=other_prospect_id, event_type="created",
    )
    log_event(
        db_session, client_id=client_id, agent="prospection", entity_type="prospect",
        entity_id=prospect_id, event_type="contact_proposed",
    )

    pipeline = get_prospect_pipeline(prospect_id, db=db_session)

    assert [e.event_type for e in pipeline] == ["created", "contact_proposed"]
