import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from agents.creation_site import agent as site_agent
from agents.creation_site import storage
from agents.creation_site.brief import SiteBrief
from agents.creation_site.content import ContentGenerationError, SiteContent
from agents.creation_site.render import render_site
from app.auth import get_current_client
from platform_core.activity import log_event
from platform_core.db import get_db
from platform_core.models import Client, Site, SiteStatus

router = APIRouter(prefix="/api/sites", tags=["sites"])


def _get_owned_site(site_id: uuid.UUID, current_client: Client, db: Session) -> Site:
    """Charge le site et vérifie qu'il appartient bien au client authentifié.

    Cloisonnement strict entre clients (CLAUDE.md §5) : un client ne doit jamais pouvoir
    lire ou modifier le site d'un autre, même en devinant un UUID.
    """
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site introuvable")
    if site.client_id != current_client.id:
        raise HTTPException(status_code=403, detail="Ce site n'appartient pas au client authentifié")
    return site


@router.post("", status_code=201)
def create_site(
    brief: SiteBrief,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> dict:
    site = Site(
        client_id=current_client.id, sector=brief.sector.value, brief=brief.model_dump(mode="json")
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    log_event(
        db,
        client_id=current_client.id,
        agent="creation_site",
        entity_type="site",
        entity_id=site.id,
        event_type="created",
    )
    return {"id": str(site.id), "status": site.status.value}


@router.post("/{site_id}/generate")
def generate_site(
    site_id: uuid.UUID,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> dict:
    site = _get_owned_site(site_id, current_client, db)

    brief = SiteBrief.model_validate(site.brief)
    try:
        content = site_agent.generate_draft_site(site.id, brief)
    except ContentGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    site.content = content.model_dump(mode="json")
    db.commit()
    log_event(
        db,
        client_id=current_client.id,
        agent="creation_site",
        entity_type="site",
        entity_id=site.id,
        event_type="content_generated",
    )
    return {"id": str(site.id), "status": site.status.value}


@router.get("/{site_id}/preview", response_class=HTMLResponse)
def preview_site(
    site_id: uuid.UUID,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> str:
    site = _get_owned_site(site_id, current_client, db)
    if site.content is None:
        raise HTTPException(status_code=409, detail="Contenu pas encore généré pour ce site")

    brief = SiteBrief.model_validate(site.brief)
    content = SiteContent.model_validate(site.content)
    return render_site(brief, content)


@router.post("/{site_id}/publish")
def publish_site(
    site_id: uuid.UUID,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> dict:
    site = _get_owned_site(site_id, current_client, db)

    # Idempotent : publier un site déjà publié ne refait pas la promotion R2 (pas d'erreur),
    # ni une nouvelle entrée dans le journal d'activité.
    if site.status != SiteStatus.published:
        storage.promote_to_live(site.id)
        site.status = SiteStatus.published
        site.published_at = datetime.now(UTC)
        db.commit()
        log_event(
            db,
            client_id=current_client.id,
            agent="creation_site",
            entity_type="site",
            entity_id=site.id,
            event_type="published",
        )

    return {"id": str(site.id), "status": site.status.value}
