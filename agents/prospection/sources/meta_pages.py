"""Recherche de prospects via l'API Meta Graph (Pages professionnelles publiques).

Deuxième source officielle en plus de Google Places (agents/prospection/skills/README.md,
"sources autorisées") : permet de trouver des établissements présents sur Facebook/Instagram
mais absents de Google Places (ou l'inverse), pour une couverture plus large — jamais un
scraping de pages, l'API Graph officielle uniquement.

Note d'honnêteté (même esprit que google_places.py, security_scan.py, le webhook Sentry de
l'agent Maintenance) : l'endpoint de recherche de Pages ("Page Public Content Access") est
une permission Meta à accès restreint (revue d'app requise par Meta), pas garantie
disponible même avec des identifiants d'app valides — le schéma de réponse suivi ci-dessous
suit la documentation Graph API au moment de l'écriture, jamais vérifié contre un appel réel
dans cette session (pas d'app Meta disponible). À valider avant tout usage en production.
"""

from typing import Any

import httpx

from agents.prospection.sources.google_places import RawPlaceResult
from platform_core.config import settings

_GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
_FIELDS = "name,phone,website,location,overall_star_rating,rating_count"


def _app_access_token() -> str:
    # Format standard Meta pour un jeton d'accès applicatif (pas un jeton utilisateur/page) :
    # suffisant pour interroger des Pages publiques, jamais pour publier en leur nom.
    return f"{settings.meta_app_id}|{settings.meta_app_secret}"


def _parse_page(page: dict[str, Any]) -> RawPlaceResult:
    location = page.get("location") or {}
    address_parts = [location.get("street"), location.get("city"), location.get("country")]
    formatted_address = ", ".join(part for part in address_parts if part) or None

    return RawPlaceResult(
        name=page.get("name", "Établissement sans nom"),
        formatted_address=formatted_address,
        phone_number=page.get("phone"),
        # Le champ `website` (site externe du commerce), jamais `link` (l'URL de la Page
        # Facebook elle-même) : confondre les deux ferait visiter facebook.com dans
        # agents/prospection/website_audit.py, qui évaluerait alors le site de Meta plutôt
        # que celui du prospect.
        website_uri=page.get("website"),
        rating=page.get("overall_star_rating"),
        user_rating_count=page.get("rating_count"),
    )


def search_pages(query: str, *, http_client: httpx.Client | None = None) -> list[RawPlaceResult]:
    """Retourne une liste vide (pas d'erreur) si `meta_app_id`/`meta_app_secret` ne sont pas
    configurés — Meta reste une source secondaire, jamais bloquante pour Google Places."""
    if not settings.meta_app_id or not settings.meta_app_secret:
        return []

    client = http_client or httpx.Client()
    response = client.get(
        f"{_GRAPH_API_BASE}/pages/search",
        params={"q": query, "fields": _FIELDS, "access_token": _app_access_token()},
    )
    response.raise_for_status()
    payload = response.json()
    return [_parse_page(page) for page in payload.get("data", [])]
