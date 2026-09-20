"""Chiffrement au repos des tokens sensibles (Client.meta_page_access_token,
Client.whatsapp_access_token — voir platform_core/models.py::EncryptedString).

Fernet (AES-128-CBC + HMAC, via `cryptography`) : symétrique, authentifié, suffisant pour
un secret que la plateforme doit pouvoir déchiffrer elle-même (pas un hash à sens unique
comme les clés API client, voir platform_core/auth.py).

Dégradation explicite : si `TOKEN_ENCRYPTION_KEY` n'est pas configurée (settings.token_encryption_key
vide), `encrypt_token`/`decrypt_token` deviennent des passe-plats (retournent la valeur
telle quelle) plutôt que de lever une exception — pour ne pas casser le développement local
ni la suite de tests tant que la clé n'est pas générée/configurée. En production, la clé
doit impérativement être configurée (voir config/credentials/README.md).
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from platform_core.config import settings


class TokenDecryptionError(Exception):
    """Levée quand une valeur chiffrée ne peut pas être déchiffrée avec la clé configurée."""


def _fernet() -> Fernet | None:
    # Pas de mise en cache : `settings.token_encryption_key` peut être modifiée à l'exécution
    # (ex. monkeypatch dans les tests) et la fonction doit refléter la valeur courante plutôt
    # qu'une clé figée au premier appel.
    if not settings.token_encryption_key:
        return None
    return Fernet(settings.token_encryption_key.encode("utf-8"))


def encrypt_token(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    fernet = _fernet()
    if fernet is None:
        return plaintext
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_token(ciphertext: str | None) -> str | None:
    if ciphertext is None:
        return None
    fernet = _fernet()
    if fernet is None:
        return ciphertext
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise TokenDecryptionError(
            "Impossible de déchiffrer la valeur : clé TOKEN_ENCRYPTION_KEY incorrecte ou "
            "valeur stockée en clair avant activation du chiffrement."
        ) from exc
