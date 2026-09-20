from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from platform_core.auth import create_client_with_api_key
from platform_core.db import get_db

router = APIRouter(prefix="/api/clients", tags=["clients"])


class ClientCreate(BaseModel):
    name: str
    sector: str
    country: str = "GA"
    currency: str = "XAF"


@router.post("", status_code=201)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)) -> dict:
    client, api_key = create_client_with_api_key(
        db, name=payload.name, sector=payload.sector, country=payload.country, currency=payload.currency
    )
    # La clé API n'est retournée qu'ici, une seule fois — à conserver côté client, jamais
    # récupérable ensuite (voir platform_core/auth.py).
    return {"id": str(client.id), "api_key": api_key}
