"""Vue agrégée des informations utiles au projet d'un client — "office manager" (extension
de Planning, décision actée avec l'utilisateur, voir MEMORY.md).

Regroupe ce qui existe déjà ailleurs (brief du site, ton de marque, contact, statut des
accès réseaux) plutôt que de dupliquer une nouvelle source de vérité — même principe que
`dashboard.py`/`onboarding.py`. Seul `project_notes` est propre à ce module : une note libre
que rien d'autre ne capture.
"""

import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.creation_site.brief import SiteBrief
from agents.planning.network_access import get_network_access_status
from platform_core.models import Client, Site


class ClientNotFoundError(RuntimeError):
    pass


class ProjectInfo(BaseModel):
    client_id: uuid.UUID
    business_name: str
    sector: str
    contact_phone: str | None
    brand_voice: str | None
    site_description: str | None
    meta_connected: bool
    whatsapp_connected: bool
    project_notes: str | None


def _get_client(client_id: uuid.UUID, *, db: Session) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise ClientNotFoundError(f"Client introuvable : {client_id}")
    return client


def get_project_info(client_id: uuid.UUID, *, db: Session) -> ProjectInfo:
    client = _get_client(client_id, db=db)

    site = db.query(Site).filter(Site.client_id == client_id).order_by(Site.created_at).first()
    site_description = SiteBrief.model_validate(site.brief).description if site is not None else None

    access_status = get_network_access_status(client_id, db=db)

    return ProjectInfo(
        client_id=client.id,
        business_name=client.name,
        sector=client.sector,
        contact_phone=client.contact_phone,
        brand_voice=client.brand_voice,
        site_description=site_description,
        meta_connected=access_status.meta_connected,
        whatsapp_connected=access_status.whatsapp_connected,
        project_notes=client.project_notes,
    )


def update_project_notes(client_id: uuid.UUID, notes: str, *, db: Session) -> ProjectInfo:
    client = _get_client(client_id, db=db)
    client.project_notes = notes
    db.commit()
    return get_project_info(client_id, db=db)
