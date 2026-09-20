import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.prospection import agent as prospection_agent
from agents.prospection import whatsapp
from agents.prospection.content import ContentGenerationError, generate_contact_message
from agents.prospection.offer import default_highlights_for_pack, generate_offer_pdf
from app.auth import get_current_client
from platform_core.activity import log_event
from platform_core.db import get_db
from platform_core.models import Client, ContactStatus, Pack, Prospect, ProspectCategory

router = APIRouter(prefix="/api/prospects", tags=["prospection"])

_BLOCKED_CATEGORIES = {ProspectCategory.non_favorable, ProspectCategory.non_joignable}


class SearchRequest(BaseModel):
    query: str
    sector: str


def _get_owned_prospect(prospect_id: uuid.UUID, current_client: Client, db: Session) -> Prospect:
    prospect = db.get(Prospect, prospect_id)
    if prospect is None:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    if prospect.client_id != current_client.id:
        raise HTTPException(status_code=403, detail="Ce prospect n'appartient pas au client authentifié")
    return prospect


def _serialize(prospect: Prospect) -> dict:
    return {
        "id": str(prospect.id),
        "business_name": prospect.business_name,
        "sector": prospect.sector,
        "category": prospect.category.value,
        "score": prospect.score,
        "contact_status": prospect.contact_status.value,
    }


@router.post("/search", status_code=201)
def search_prospects(
    payload: SearchRequest, current_client: Client = Depends(get_current_client), db: Session = Depends(get_db)
) -> list[dict]:
    prospects = prospection_agent.search_and_score(current_client.id, payload.query, payload.sector, db=db)
    return [_serialize(p) for p in prospects]


@router.get("")
def list_prospects(current_client: Client = Depends(get_current_client), db: Session = Depends(get_db)) -> list[dict]:
    prospects = db.query(Prospect).filter(Prospect.client_id == current_client.id).order_by(Prospect.created_at.desc()).all()
    return [_serialize(p) for p in prospects]


@router.post("/{prospect_id}/propose-contact")
def propose_contact(
    prospect_id: uuid.UUID, current_client: Client = Depends(get_current_client), db: Session = Depends(get_db)
) -> dict:
    prospect = _get_owned_prospect(prospect_id, current_client, db)

    if prospect.category in _BLOCKED_CATEGORIES:
        raise HTTPException(
            status_code=403,
            detail=f"Interdit : prospect classé '{prospect.category.value}' (CLAUDE.md §5)",
        )
    if prospect.contact_status != ContactStatus.none:
        raise HTTPException(
            status_code=409,
            detail=f"Action impossible : statut actuel '{prospect.contact_status.value}', 'none' requis",
        )

    likely_needs = (
        "Digitalisation de sa présence en ligne (site web, réseaux sociaux)"
        if not prospect.raw_data.get("website_uri")
        else "Amélioration de sa présence digitale existante"
    )

    try:
        message = generate_contact_message(
            prospect.business_name, prospect.sector, likely_needs, current_client.brand_voice
        )
    except ContentGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    prospect.contact_message = message.model_dump(mode="json")
    prospect.contact_status = ContactStatus.pending_validation
    db.commit()
    log_event(
        db,
        client_id=current_client.id,
        agent="prospection",
        entity_type="prospect",
        entity_id=prospect.id,
        event_type="contact_proposed",
    )
    return {"id": str(prospect.id), "contact_status": prospect.contact_status.value, "message": message.message}


@router.post("/{prospect_id}/validate-contact")
def validate_contact(
    prospect_id: uuid.UUID, current_client: Client = Depends(get_current_client), db: Session = Depends(get_db)
) -> dict:
    prospect = _get_owned_prospect(prospect_id, current_client, db)
    if prospect.contact_status != ContactStatus.pending_validation:
        raise HTTPException(
            status_code=409,
            detail=f"Action impossible : statut actuel '{prospect.contact_status.value}', 'pending_validation' requis",
        )

    prospect.contact_status = ContactStatus.validated
    db.commit()
    log_event(
        db,
        client_id=current_client.id,
        agent="prospection",
        entity_type="prospect",
        entity_id=prospect.id,
        event_type="contact_validated",
    )
    return {"id": str(prospect.id), "contact_status": prospect.contact_status.value}


@router.post("/{prospect_id}/send-contact")
def send_contact(
    prospect_id: uuid.UUID, current_client: Client = Depends(get_current_client), db: Session = Depends(get_db)
) -> dict:
    prospect = _get_owned_prospect(prospect_id, current_client, db)

    # Défense en profondeur : re-vérifié même si /propose-contact l'a déjà bloqué en amont.
    if prospect.category in _BLOCKED_CATEGORIES:
        raise HTTPException(
            status_code=403,
            detail=f"Interdit : prospect classé '{prospect.category.value}' (CLAUDE.md §5)",
        )
    if prospect.contact_status != ContactStatus.validated:
        raise HTTPException(
            status_code=409,
            detail=f"Action impossible : statut actuel '{prospect.contact_status.value}', 'validated' requis",
        )
    if not current_client.whatsapp_phone_number_id or not current_client.whatsapp_access_token:
        raise HTTPException(
            status_code=412,
            detail="Aucun numéro WhatsApp Business connecté pour ce client",
        )
    if not prospect.phone:
        raise HTTPException(status_code=422, detail="Ce prospect n'a pas de numéro de téléphone")

    try:
        whatsapp.send_whatsapp_message(
            current_client.whatsapp_phone_number_id,
            current_client.whatsapp_access_token,
            prospect.phone,
            prospect.contact_message["message"],
        )
    except whatsapp.WhatsAppSendError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    prospect.contact_status = ContactStatus.sent
    prospect.contacted_at = datetime.now(UTC)
    db.commit()
    log_event(
        db,
        client_id=current_client.id,
        agent="prospection",
        entity_type="prospect",
        entity_id=prospect.id,
        event_type="contact_sent",
    )
    return {"id": str(prospect.id), "contact_status": prospect.contact_status.value}


@router.get("/{prospect_id}/offer")
def get_offer(
    prospect_id: uuid.UUID, current_client: Client = Depends(get_current_client), db: Session = Depends(get_db)
) -> Response:
    prospect = _get_owned_prospect(prospect_id, current_client, db)

    pack = current_client.subscription.pack if current_client.subscription else Pack.starter
    pdf_bytes = generate_offer_pdf(prospect.business_name, pack, default_highlights_for_pack(pack))

    return Response(content=pdf_bytes, media_type="application/pdf")
