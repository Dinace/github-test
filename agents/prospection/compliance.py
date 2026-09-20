"""Garde-fou de conformité des sources de collecte.

Applique EN CODE la règle "LinkedIn interdit, sans exception" (agents/prospection/skills/
README.md), plutôt que de compter uniquement sur la documentation — un futur appel de
collecte qui oublierait de vérifier la liste blanche est bloqué ici, pas seulement rappelé
dans un commentaire. Toute fonction de collecte HTTP de ce package doit appeler
`assert_source_allowed` avant la moindre requête.
"""

from urllib.parse import urlparse

FORBIDDEN_DOMAINS = frozenset({"linkedin.com"})


class ForbiddenSourceError(RuntimeError):
    """Levée quand une URL de collecte correspond à une source explicitement interdite."""


def assert_source_allowed(url: str) -> None:
    host = urlparse(url).netloc.lower()
    if any(host == domain or host.endswith(f".{domain}") for domain in FORBIDDEN_DOMAINS):
        raise ForbiddenSourceError(
            f"Source interdite (agents/prospection/skills/README.md, aucune exception) : {url}"
        )
