import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from platform_core.config import settings
from platform_core.db import Base
from platform_core.encryption import TokenDecryptionError, decrypt_token, encrypt_token
from platform_core.models import Client


def test_encrypt_token_is_passthrough_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "token_encryption_key", "")

    assert encrypt_token("secret-token") == "secret-token"
    assert decrypt_token("secret-token") == "secret-token"


def test_encrypt_token_round_trip_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "token_encryption_key", Fernet.generate_key().decode("utf-8"))

    ciphertext = encrypt_token("secret-token")

    assert ciphertext != "secret-token"
    assert decrypt_token(ciphertext) == "secret-token"


def test_decrypt_token_with_wrong_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "token_encryption_key", Fernet.generate_key().decode("utf-8"))
    ciphertext = encrypt_token("secret-token")

    monkeypatch.setattr(settings, "token_encryption_key", Fernet.generate_key().decode("utf-8"))

    with pytest.raises(TokenDecryptionError):
        decrypt_token(ciphertext)


def test_client_access_tokens_are_encrypted_at_rest(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "token_encryption_key", Fernet.generate_key().decode("utf-8"))
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        client = Client(name="Chez Awa", sector="restaurant", api_key_hash="x", meta_page_access_token="raw-meta-token")
        session.add(client)
        session.commit()
        client_id = client.id

    # Lecture de la valeur brute stockée en base (colonne texte, en contournant l'ORM/le
    # TypeDecorator) : elle ne doit jamais contenir le texte en clair.
    with engine.connect() as conn:
        raw_value = conn.exec_driver_sql("SELECT meta_page_access_token FROM clients").scalar_one()
    assert raw_value != "raw-meta-token"

    with Session(engine) as session:
        reloaded = session.execute(select(Client).where(Client.id == client_id)).scalar_one()
        assert reloaded.meta_page_access_token == "raw-meta-token"
