import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.planning.network_access import (
    ClientNotFoundError,
    NetworkAccessUpdate,
    get_network_access_status,
    set_network_access,
)
from platform_core.auth import create_client_with_api_key
from platform_core.db import Base
from platform_core.models import Client


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


def test_status_is_disconnected_by_default(db_session: Session, client_id: uuid.UUID) -> None:
    status = get_network_access_status(client_id, db=db_session)

    assert status.meta_connected is False
    assert status.whatsapp_connected is False


def test_set_network_access_marks_meta_connected(db_session: Session, client_id: uuid.UUID) -> None:
    status = set_network_access(
        client_id,
        NetworkAccessUpdate(meta_page_id="123456", meta_page_access_token="secret-token"),
        db=db_session,
    )

    assert status.meta_connected is True
    assert status.whatsapp_connected is False


def test_set_network_access_encrypts_token_at_rest(db_session: Session, client_id: uuid.UUID) -> None:
    """La colonne EncryptedString existe déjà (voir platform_core/encryption.py) : ce test
    vérifie seulement que set_network_access écrit bien dedans, pas le chiffrement lui-même
    (déjà couvert par tests/test_encryption.py)."""
    set_network_access(
        client_id,
        NetworkAccessUpdate(meta_page_id="123456", meta_page_access_token="secret-token"),
        db=db_session,
    )

    reloaded = db_session.get(Client, client_id)
    assert reloaded.meta_page_access_token == "secret-token"  # déchiffré à la lecture via l'ORM


def test_set_network_access_partial_update_does_not_erase_other_fields(
    db_session: Session, client_id: uuid.UUID
) -> None:
    set_network_access(
        client_id,
        NetworkAccessUpdate(meta_page_id="123456", meta_page_access_token="secret-token"),
        db=db_session,
    )

    # Deuxième appel : seulement le token (ex. rotation) -> meta_page_id doit rester intact.
    set_network_access(
        client_id, NetworkAccessUpdate(meta_page_access_token="new-secret-token"), db=db_session
    )

    reloaded = db_session.get(Client, client_id)
    assert reloaded.meta_page_id == "123456"
    assert reloaded.meta_page_access_token == "new-secret-token"


def test_set_network_access_raises_for_unknown_client(db_session: Session) -> None:
    with pytest.raises(ClientNotFoundError):
        set_network_access(uuid.uuid4(), NetworkAccessUpdate(meta_page_id="x"), db=db_session)
