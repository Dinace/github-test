"""Point d'entrée de l'agent Prospection : recherche -> signaux -> scoring -> fiches."""

import uuid

import httpx
from sqlalchemy.orm import Session

from agents.prospection.scoring import ProspectSignals, WebsiteStatus, score_prospect
from agents.prospection.sources.google_places import RawPlaceResult, search_places
from platform_core.models import Prospect


def _signals_from_place(place: RawPlaceResult) -> ProspectSignals:
    """Dérive des signaux de scoring à partir d'un résultat Google Places.

    Simplification assumée (voir agents/prospection/skills/README.md, points ouverts) : la
    présence d'un `website_uri` est traitée comme un site "moderne" (Google Places ne dit
    pas si un site est à jour) ; son absence comme "none". Distinguer "outdated"
    nécessiterait de visiter le site, pas fait ici.
    """
    website_status = WebsiteStatus.modern if place.website_uri else WebsiteStatus.none
    has_recent_activity = bool(place.rating and place.user_rating_count)

    return ProspectSignals(
        has_valid_contact=bool(place.phone_number),
        website_status=website_status,
        # La recherche cible déjà un secteur donné (requête construite par l'appelant) :
        # tout résultat retourné correspond par construction au secteur recherché.
        sector_matches_catalog=True,
        has_recent_activity_signal=has_recent_activity,
    )


def search_and_score(
    client_id: uuid.UUID, query: str, sector: str, *, db: Session, http_client: httpx.Client | None = None
) -> list[Prospect]:
    """Recherche des prospects via Google Places, les score, et crée les fiches en base."""
    places = search_places(query, http_client=http_client)

    prospects = []
    for place in places:
        signals = _signals_from_place(place)
        category, score = score_prospect(signals)

        prospect = Prospect(
            client_id=client_id,
            business_name=place.name,
            sector=sector,
            phone=place.phone_number,
            source="google_places",
            raw_data=place.model_dump(mode="json"),
            category=category,
            score=score,
        )
        db.add(prospect)
        prospects.append(prospect)

    db.commit()
    for prospect in prospects:
        db.refresh(prospect)
    return prospects
