"""Point d'entrée de l'agent Création de site : brief -> contenu -> rendu -> brouillon R2."""

import uuid
from typing import Any

import anthropic

from agents.creation_site.brief import SiteBrief
from agents.creation_site.content import SiteContent, generate_content
from agents.creation_site.render import render_site
from agents.creation_site.storage import upload_draft


def generate_draft_site(
    site_id: uuid.UUID,
    brief: SiteBrief,
    *,
    client: anthropic.Anthropic | None = None,
    s3_client: Any = None,
) -> SiteContent:
    """Génère le contenu, rend le HTML et l'écrit en brouillon sur Cloudflare R2.

    Retourne le contenu structuré (source de vérité stockée en base) ; le HTML est un
    artefact dérivé, régénérable à tout moment via render_site(brief, content).
    """
    content = generate_content(brief, client=client)
    html = render_site(brief, content)
    upload_draft(site_id, html, s3_client=s3_client)
    return content
