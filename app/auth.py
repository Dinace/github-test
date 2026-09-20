from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from platform_core.auth import hash_api_key
from platform_core.config import settings
from platform_core.db import get_db
from platform_core.models import Client


def get_current_client(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> Client:
    """Résout le client authentifié à partir de `Authorization: Bearer <clé API>`."""
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="En-tête Authorization: Bearer <clé API> requis")

    api_key = authorization.removeprefix("Bearer ").strip()
    client = db.query(Client).filter(Client.api_key_hash == hash_api_key(api_key)).first()
    if client is None:
        raise HTTPException(status_code=401, detail="Clé API invalide")

    return client


def require_ops_token(authorization: str | None = Header(default=None)) -> None:
    """Verrou minimal pour les endpoints internes staff de l'agent Maintenance.

    STOPGAP explicite (voir platform_core/config.py) : un jeton partagé unique n'est pas un
    vrai système d'authentification staff (pas de comptes individuels, pas de rôles, pas
    d'audit par utilisateur). Suffisant pour débloquer l'implémentation de l'agent, pas pour
    une vraie mise en production multi-opérateurs.
    """
    if not settings.ops_api_token:
        raise HTTPException(status_code=503, detail="OPS_API_TOKEN non configuré côté serveur")
    if authorization != f"Bearer {settings.ops_api_token}":
        raise HTTPException(status_code=401, detail="Jeton d'opération invalide")
