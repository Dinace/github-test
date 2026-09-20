"""Authentification par clé API pour les endpoints propres à un client.

Choix : une clé API aléatoire à haute entropie (`secrets.token_urlsafe`), hachée en SHA-256
avant stockage. SHA-256 (et non bcrypt/argon2) est correct ici précisément parce que la clé
est déjà un secret de 256 bits généré aléatoirement, pas un mot de passe choisi par un
humain à faible entropie — une attaque par force brute sur le hash n'est pas plus praticable
qu'une attaque directe sur la clé elle-même. bcrypt/argon2 seraient nécessaires si on hachait
un mot de passe humain (pas le cas ici).

Portée volontairement limitée : ceci authentifie un *client* de la plateforme pour les
endpoints qui lui sont propres (ex. ses sites). Ce n'est pas un système de login humain avec
session/mot de passe pour le dashboard — ce dernier reste à concevoir séparément et pourra
réutiliser ce même modèle Client une fois construit.
"""

import hashlib
import hmac
import secrets

from sqlalchemy.orm import Session

from platform_core.models import Client


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(api_key: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(api_key), expected_hash)


def create_client_with_api_key(
    db: Session, *, name: str, sector: str, country: str = "GA", currency: str = "XAF"
) -> tuple[Client, str]:
    """Crée un client et sa clé API.

    La clé en clair n'est retournée qu'une seule fois ici (jamais stockée ni journalisée
    au-delà de cet appel) — convention standard pour les clés API (ex. Stripe, GitHub).
    """
    api_key = generate_api_key()
    client = Client(
        name=name,
        sector=sector,
        country=country,
        currency=currency,
        api_key_hash=hash_api_key(api_key),
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client, api_key
