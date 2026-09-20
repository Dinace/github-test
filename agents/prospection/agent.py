"""Point d'entrée de l'agent Prospection : recherche -> signaux -> scoring -> fiches."""

import uuid

import httpx
from sqlalchemy.orm import Session

from agents.prospection.matching import normalize_business_name
from agents.prospection.scoring import ProspectSignals, WebsiteStatus, score_prospect
from agents.prospection.sources.google_places import RawPlaceResult, search_places
from agents.prospection.sources.meta_pages import search_pages
from agents.prospection.website_audit import assess_website
from platform_core.activity import log_event
from platform_core.models import Prospect


def _merge_sources(
    places: list[RawPlaceResult], pages: list[RawPlaceResult]
) -> list[tuple[RawPlaceResult, str]]:
    """Combine les deux sources, dédupliquées par numéro de téléphone d'abord (signal
    d'identité le plus fiable entre deux API différentes), puis par nom normalisé
    (agents/prospection/matching.py — correspondance exacte après normalisation, jamais de
    similarité floue, voir la justification dans ce module) pour les établissements sans
    téléphone commun. Google Places reste prioritaire à égalité de résultat : ordre d'appel
    dans `search_and_score`, jamais l'inverse."""
    seen_phones = {place.phone_number for place in places if place.phone_number}
    seen_names = {normalize_business_name(place.name) for place in places}
    merged = [(place, "google_places") for place in places]
    for page in pages:
        if page.phone_number and page.phone_number in seen_phones:
            continue
        if normalize_business_name(page.name) in seen_names:
            continue
        merged.append((page, "meta_pages"))
        if page.phone_number:
            seen_phones.add(page.phone_number)
        seen_names.add(normalize_business_name(page.name))
    return merged


def _signals_from_place(place: RawPlaceResult, *, website_http_client: httpx.Client | None = None) -> ProspectSignals:
    """Dérive des signaux de scoring à partir d'un résultat de recherche (Google Places ou
    Meta Pages — même type `RawPlaceResult`, la source d'origine ne change pas la façon de
    calculer les signaux).

    `website_status` visite réellement le site (agents/prospection/website_audit.py) quand
    un `website_uri` existe — comble l'ancienne simplification "présence = moderne" (ni
    Google Places ni Meta ne disent si un site est à jour). Absence de `website_uri` :
    `none` directement, pas de visite à faire.
    """
    if place.website_uri:
        website_status = assess_website(place.website_uri, http_client=website_http_client)
    else:
        website_status = WebsiteStatus.none
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
    client_id: uuid.UUID,
    query: str,
    sector: str,
    *,
    db: Session,
    http_client: httpx.Client | None = None,
    website_http_client: httpx.Client | None = None,
    meta_http_client: httpx.Client | None = None,
) -> list[Prospect]:
    """Recherche des prospects via Google Places et Meta Pages, les score, et crée les
    fiches en base.

    `http_client` (Google Places), `meta_http_client` (Meta Pages) et `website_http_client`
    (visite des sites trouvés) sont injectables séparément : trois intégrations techniques
    distinctes, avec des besoins de test différents — les confondre rendrait chacune plus
    difficile à tester isolément. Meta Pages est une source secondaire silencieuse : sans
    `meta_app_id`/`meta_app_secret` configurés, `search_pages` retourne une liste vide sans
    erreur (voir agents/prospection/sources/meta_pages.py), la recherche continue sur
    Google Places seul.
    """
    places = search_places(query, http_client=http_client)
    pages = search_pages(query, http_client=meta_http_client)
    results = _merge_sources(places, pages)

    prospects = []
    for result, source in results:
        signals = _signals_from_place(result, website_http_client=website_http_client)
        category, score = score_prospect(signals)

        prospect = Prospect(
            client_id=client_id,
            business_name=result.name,
            sector=sector,
            phone=result.phone_number,
            source=source,
            raw_data=result.model_dump(mode="json"),
            category=category,
            score=score,
        )
        db.add(prospect)
        prospects.append(prospect)

    db.commit()
    for prospect in prospects:
        db.refresh(prospect)
        # Alimente l'historique lu par l'agent Planning (platform_core.activity) — Prospection
        # ne journalise que ses propres événements, jamais les données d'un autre agent.
        log_event(
            db,
            client_id=client_id,
            agent="prospection",
            entity_type="prospect",
            entity_id=prospect.id,
            event_type="created",
            details={"category": prospect.category.value, "score": prospect.score},
        )
    return prospects
