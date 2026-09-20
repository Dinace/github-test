"""Recherche de prospects via Google Places API (source officielle prioritaire).

agents/prospection/skills/README.md : privilégier une API officielle plutôt que le
scraping. Utilise l'API "Places API (New)" (`places:searchText`), pas l'ancienne Places API
legacy.

Note d'honnêteté (même esprit que security_scan.py et le webhook Sentry de l'agent
Maintenance) : les noms de champs exacts de la réponse ci-dessous suivent le schéma
documenté par Google au moment de l'écriture, mais n'ont pas été vérifiés contre un appel
réel dans cette session (pas de clé API disponible) — à confirmer avant un premier usage en
production.
"""

from typing import Any

import httpx
from pydantic import BaseModel

from platform_core.config import settings

_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_FIELD_MASK = (
    "places.displayName,places.formattedAddress,places.nationalPhoneNumber,"
    "places.websiteUri,places.rating,places.userRatingCount"
)


class RawPlaceResult(BaseModel):
    name: str
    formatted_address: str | None = None
    phone_number: str | None = None
    website_uri: str | None = None
    rating: float | None = None
    user_rating_count: int | None = None


def _parse_place(place: dict[str, Any]) -> RawPlaceResult:
    return RawPlaceResult(
        name=place.get("displayName", {}).get("text", "Établissement sans nom"),
        formatted_address=place.get("formattedAddress"),
        phone_number=place.get("nationalPhoneNumber"),
        website_uri=place.get("websiteUri"),
        rating=place.get("rating"),
        user_rating_count=place.get("userRatingCount"),
    )


def search_places(query: str, *, http_client: httpx.Client | None = None) -> list[RawPlaceResult]:
    client = http_client or httpx.Client()
    response = client.post(
        _SEARCH_URL,
        json={"textQuery": query},
        headers={
            "X-Goog-Api-Key": settings.google_places_api_key,
            "X-Goog-FieldMask": _FIELD_MASK,
        },
    )
    response.raise_for_status()
    payload = response.json()
    return [_parse_place(place) for place in payload.get("places", [])]
