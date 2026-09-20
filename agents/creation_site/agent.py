"""Point d'entrée de l'agent Création de site : brief -> contenu -> rendu -> brouillon."""

import uuid

import anthropic

from agents.creation_site.brief import SiteBrief
from agents.creation_site.content import SiteContent, generate_content
from agents.creation_site.publish import write_draft
from agents.creation_site.render import render_site


def generate_draft_site(
    site_id: uuid.UUID, brief: SiteBrief, *, client: anthropic.Anthropic | None = None
) -> SiteContent:
    """Génère le contenu, rend le HTML et l'écrit en brouillon.

    Retourne le contenu structuré (source de vérité stockée en base) ; le HTML est un
    artefact dérivé, régénérable à tout moment via render_site(brief, content).
    """
    content = generate_content(brief, client=client)
    html = render_site(brief, content)
    write_draft(site_id, html)
    return content
