from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from platform_core.auth import hash_api_key
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
