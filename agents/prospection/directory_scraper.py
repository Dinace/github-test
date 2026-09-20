"""Collecte HTML basique sur des annuaires professionnels publics (BeautifulSoup).

Réservé aux sources HTML classiques listées comme autorisées (agents/prospection/skills/
README.md) : chambres de commerce, registres publics. Vérifie systématiquement
agents.prospection.compliance avant toute requête.
"""

import httpx
from bs4 import BeautifulSoup

from agents.prospection.compliance import assert_source_allowed


def fetch_directory_page(url: str, *, http_client: httpx.Client | None = None) -> BeautifulSoup:
    assert_source_allowed(url)
    client = http_client or httpx.Client()
    response = client.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")
