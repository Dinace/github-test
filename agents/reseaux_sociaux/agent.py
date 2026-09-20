"""Point d'entrée de l'agent Réseaux sociaux : brief -> contenu généré."""

import anthropic

from agents.reseaux_sociaux.brief import PostBrief
from agents.reseaux_sociaux.content import PostContent, generate_content


def generate_draft_content(
    brief: PostBrief, brand_voice: str | None, *, client: anthropic.Anthropic | None = None
) -> PostContent:
    """Génère le contenu texte de la publication. Le contenu est la source de vérité,
    stocké en base (platform_core.models.Post.content) — pas d'artefact dérivé à écrire
    ailleurs, contrairement à l'agent Création de site (pas de rendu/stockage de fichier)."""
    return generate_content(brief, brand_voice, client=client)
