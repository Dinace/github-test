import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from agents.creation_site import agent as site_agent
from agents.creation_site.brief import SiteBrief
from agents.creation_site.content import ContentGenerationError, SiteContent
from agents.creation_site.render import render_site
from platform_core.db import get_db
from platform_core.models import Site, SiteStatus

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.post("", status_code=201)
def create_site(brief: SiteBrief, client_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    site = Site(client_id=client_id, sector=brief.sector.value, brief=brief.model_dump(mode="json"))
    db.add(site)
    db.commit()
    db.refresh(site)
    return {"id": str(site.id), "status": site.status.value}


@router.post("/{site_id}/generate")
def generate_site(site_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site introuvable")

    brief = SiteBrief.model_validate(site.brief)
    try:
        content = site_agent.generate_draft_site(site.id, brief)
    except ContentGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    site.content = content.model_dump(mode="json")
    db.commit()
    return {"id": str(site.id), "status": site.status.value}


@router.get("/{site_id}/preview", response_class=HTMLResponse)
def preview_site(site_id: uuid.UUID, db: Session = Depends(get_db)) -> str:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site introuvable")
    if site.content is None:
        raise HTTPException(status_code=409, detail="Contenu pas encore généré pour ce site")

    brief = SiteBrief.model_validate(site.brief)
    content = SiteContent.model_validate(site.content)
    return render_site(brief, content)


@router.post("/{site_id}/publish")
def publish_site(site_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site introuvable")

    # Idempotent : publier un site déjà publié ne fait rien de plus (pas d'erreur).
    if site.status != SiteStatus.published:
        site.status = SiteStatus.published
        site.published_at = datetime.now(UTC)
        db.commit()

    return {"id": str(site.id), "status": site.status.value}
