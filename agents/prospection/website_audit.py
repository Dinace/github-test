"""Détection heuristique du statut d'un site web de prospect (moderne / obsolète / absent).

Comblait le point ouvert "détection réelle d'un site obsolète (nécessiterait de visiter et
analyser le site)" — jusqu'ici `agents/prospection/agent.py` traitait tout `website_uri`
non vide comme "moderne", faute de mieux (Google Places ne dit pas si un site est à jour).

Note d'honnêteté (même esprit que security_scan.py et le webhook Sentry de l'agent
Maintenance) : c'est une **heuristique**, pas un audit de conception ou de référencement —
elle peut mal classer un site inhabituel mais parfaitement à jour (ex. une SPA qui injecte
sa balise viewport en JavaScript après coup) ou, à l'inverse, un vieux site qui coche les
bonnes cases techniques par hasard. Utilisée uniquement comme signal d'entrée du scoring
(agents/prospection/scoring.py), jamais comme verdict communiqué tel quel au client.
"""

import re

import httpx

from agents.prospection.scoring import WebsiteStatus

_VIEWPORT_META_PATTERN = re.compile(r'<meta[^>]+name=["\']viewport["\']', re.IGNORECASE)

# Seuil bas : une page "en construction", un domaine parké ou une page d'erreur générique
# renvoient généralement un corps HTML minimal — un vrai site professionnel, même simple,
# dépasse largement ça (ne serait-ce qu'avec le CSS/JS inline habituel des générateurs de
# sites low-cost visés par ce marché).
_MIN_CONTENT_LENGTH = 500


def assess_website(url: str, *, http_client: httpx.Client | None = None, timeout: float = 5.0) -> WebsiteStatus:
    """Visite l'URL et retourne un statut heuristique.

    Un site injoignable (DNS, timeout, TLS, HTTP >= 400) est classé `none` plutôt
    qu'`outdated` : pour un prospect, un site cassé a le même besoin de digitalisation
    qu'un prospect sans site du tout — ce n'est pas juste "à moderniser".
    """
    client = http_client or httpx.Client()
    try:
        response = client.get(url, timeout=timeout, follow_redirects=True)
    except httpx.HTTPError:
        return WebsiteStatus.none

    if response.status_code >= 400:
        return WebsiteStatus.none

    html = response.text
    if len(html) < _MIN_CONTENT_LENGTH:
        return WebsiteStatus.outdated

    if not _VIEWPORT_META_PATTERN.search(html):
        # Absence de balise viewport = site non pensé mobile-first, signal robuste d'un site
        # ancien (standard depuis le début des années 2010, et le marché cible est
        # majoritairement mobile — voir CLAUDE.md §3, choix du dashboard).
        return WebsiteStatus.outdated

    return WebsiteStatus.modern
