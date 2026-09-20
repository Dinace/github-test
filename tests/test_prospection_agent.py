import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.prospection.agent import search_and_score
from platform_core.auth import create_client_with_api_key
from platform_core.config import settings
from platform_core.db import Base
from platform_core.models import ProspectCategory


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


class _FakeHttpClient:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def post(self, url: str, *, json: dict, headers: dict) -> _FakeResponse:
        return _FakeResponse(self._payload)


class _FakeWebsiteResponse:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text


class _FakeWebsiteHttpClient:
    """Simule la visite du site d'un prospect (agents/prospection/website_audit.py) —
    distinct de `_FakeHttpClient` ci-dessus, qui simule l'API Google Places (POST/JSON)."""

    def __init__(self, html_by_url: dict[str, str]) -> None:
        self._html_by_url = html_by_url

    def get(self, url: str, **kwargs) -> _FakeWebsiteResponse:
        return _FakeWebsiteResponse(200, self._html_by_url.get(url, ""))


class _FakeMetaHttpClient:
    """Simule l'API Meta Pages (GET/JSON) — distincte de `_FakeHttpClient` (Google Places,
    POST) et `_FakeWebsiteHttpClient` (visite de site, GET mais réponses HTML)."""

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def get(self, url: str, *, params: dict) -> _FakeResponse:
        return _FakeResponse(self._payload)


@pytest.fixture()
def db_session(tmp_path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


@pytest.fixture()
def client_id(db_session: Session) -> uuid.UUID:
    client, _api_key = create_client_with_api_key(db_session, name="Chez Awa", sector="restaurant")
    return client.id


def test_search_and_score_creates_prospects_with_categories(db_session: Session, client_id: uuid.UUID) -> None:
    payload = {
        "places": [
            {
                "displayName": {"text": "Restaurant Sans Site"},
                "nationalPhoneNumber": "+24101020304",
                "rating": 4.8,
                "userRatingCount": 30,
            },
            {"displayName": {"text": "Restaurant Sans Contact"}},
        ]
    }
    fake_http = _FakeHttpClient(payload)

    prospects = search_and_score(client_id, "restaurant Libreville", "restaurant", db=db_session, http_client=fake_http)

    assert len(prospects) == 2
    favorable = next(p for p in prospects if p.business_name == "Restaurant Sans Site")
    unreachable = next(p for p in prospects if p.business_name == "Restaurant Sans Contact")

    assert favorable.category == ProspectCategory.favorable
    assert unreachable.category == ProspectCategory.non_joignable
    assert all(p.client_id == client_id for p in prospects)
    assert all(p.source == "google_places" for p in prospects)


def test_search_and_score_visits_prospect_website_to_assess_status(
    db_session: Session, client_id: uuid.UUID
) -> None:
    """Le statut du site n'est plus déduit de la simple présence de `websiteUri` : le site
    est réellement visité (agents/prospection/website_audit.py) pour distinguer un site
    moderne d'un site obsolète."""
    payload = {
        "places": [
            {
                "displayName": {"text": "Boutique Site Moderne"},
                "nationalPhoneNumber": "+24101020304",
                "websiteUri": "https://boutique-moderne.ga",
            },
            {
                "displayName": {"text": "Boutique Vieux Site"},
                "nationalPhoneNumber": "+24101020305",
                "websiteUri": "https://vieux-site.ga",
            },
        ]
    }
    fake_http = _FakeHttpClient(payload)
    fake_website_http = _FakeWebsiteHttpClient(
        {
            "https://boutique-moderne.ga": (
                '<html><head><meta name="viewport" content="width=device-width"></head>'
                "<body>" + "<p>Contenu riche.</p>" * 50 + "</body></html>"
            ),
            "https://vieux-site.ga": "<html><body>Site minimal sans balise viewport.</body></html>",
        }
    )

    prospects = search_and_score(
        client_id,
        "boutique Libreville",
        "boutique",
        db=db_session,
        http_client=fake_http,
        website_http_client=fake_website_http,
    )

    modern = next(p for p in prospects if p.business_name == "Boutique Site Moderne")
    outdated = next(p for p in prospects if p.business_name == "Boutique Vieux Site")

    assert modern.raw_data["website_uri"] == "https://boutique-moderne.ga"
    # Un site moderne pèse négativement dans le score (voir ScoringWeights.website_modern) :
    # le prospect avec le site à jour doit scorer strictement moins bien que celui à l'ancien
    # site, preuve que la visite réelle du site a bien influencé le résultat.
    assert modern.score < outdated.score


def test_search_and_score_adds_meta_pages_results_not_found_on_google(
    db_session: Session, client_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "meta_app_id", "test-app-id")
    monkeypatch.setattr(settings, "meta_app_secret", "test-app-secret")

    google_payload = {"places": [{"displayName": {"text": "Restaurant Google"}, "nationalPhoneNumber": "+24101010101"}]}
    meta_payload = {"data": [{"name": "Boutique Meta Seule", "phone": "+24102020202"}]}

    prospects = search_and_score(
        client_id,
        "restaurant Libreville",
        "restaurant",
        db=db_session,
        http_client=_FakeHttpClient(google_payload),
        meta_http_client=_FakeMetaHttpClient(meta_payload),
    )

    assert len(prospects) == 2
    google_prospect = next(p for p in prospects if p.business_name == "Restaurant Google")
    meta_prospect = next(p for p in prospects if p.business_name == "Boutique Meta Seule")
    assert google_prospect.source == "google_places"
    assert meta_prospect.source == "meta_pages"


def test_search_and_score_deduplicates_meta_pages_by_phone(
    db_session: Session, client_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Le même établissement trouvé par les deux sources (même numéro de téléphone) ne doit
    créer qu'UNE seule fiche prospect, pas un doublon."""
    monkeypatch.setattr(settings, "meta_app_id", "test-app-id")
    monkeypatch.setattr(settings, "meta_app_secret", "test-app-secret")

    google_payload = {
        "places": [{"displayName": {"text": "Restaurant Chez Awa"}, "nationalPhoneNumber": "+24101010101"}]
    }
    meta_payload = {"data": [{"name": "Restaurant Chez Awa (Facebook)", "phone": "+24101010101"}]}

    prospects = search_and_score(
        client_id,
        "restaurant Libreville",
        "restaurant",
        db=db_session,
        http_client=_FakeHttpClient(google_payload),
        meta_http_client=_FakeMetaHttpClient(meta_payload),
    )

    assert len(prospects) == 1
    assert prospects[0].source == "google_places"
