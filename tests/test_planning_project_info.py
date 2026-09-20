import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.planning.network_access import NetworkAccessUpdate, set_network_access
from agents.planning.project_info import (
    ClientNotFoundError,
    get_project_info,
    update_project_notes,
)
from platform_core.auth import create_client_with_api_key
from platform_core.db import Base
from platform_core.models import Site


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


def test_project_info_aggregates_existing_fields(db_session: Session, client_id: uuid.UUID) -> None:
    db_session.add(
        Site(
            client_id=client_id,
            sector="restaurant",
            brief={
                "business_name": "Chez Awa",
                "sector": "restaurant",
                "description": "Restaurant familial au centre-ville",
                "phone": "+24101020304",
            },
        )
    )
    db_session.commit()

    info = get_project_info(client_id, db=db_session)

    assert info.business_name == "Chez Awa"
    assert info.sector == "restaurant"
    assert info.site_description == "Restaurant familial au centre-ville"
    assert info.meta_connected is False
    assert info.whatsapp_connected is False
    assert info.project_notes is None


def test_project_info_reflects_network_access_status(db_session: Session, client_id: uuid.UUID) -> None:
    set_network_access(
        client_id,
        NetworkAccessUpdate(meta_page_id="123456", meta_page_access_token="secret-token"),
        db=db_session,
    )

    info = get_project_info(client_id, db=db_session)

    assert info.meta_connected is True
    assert info.whatsapp_connected is False


def test_project_info_without_site_has_no_description(db_session: Session, client_id: uuid.UUID) -> None:
    info = get_project_info(client_id, db=db_session)

    assert info.site_description is None


def test_update_project_notes(db_session: Session, client_id: uuid.UUID) -> None:
    info = update_project_notes(client_id, "Préfère être contacté le matin.", db=db_session)

    assert info.project_notes == "Préfère être contacté le matin."
    assert get_project_info(client_id, db=db_session).project_notes == "Préfère être contacté le matin."


def test_get_project_info_raises_for_unknown_client(db_session: Session) -> None:
    with pytest.raises(ClientNotFoundError):
        get_project_info(uuid.uuid4(), db=db_session)
