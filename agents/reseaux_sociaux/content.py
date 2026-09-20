"""Génération du texte d'une publication réseaux sociaux à partir d'un brief.

Même choix que l'agent Création de site (agents/creation_site/content.py) : appel direct à
l'API Claude (pas le Claude Agent SDK) — génération structurée en un seul appel, pas une
tâche agentique ouverte. Corrige la mention encore présente dans
agents/reseaux_sociaux/skills/README.md ("Claude Agent SDK"), pour la même raison que
CLAUDE.md §3 documente déjà pour la Création de site.
"""

import json

import anthropic
from pydantic import BaseModel, ValidationError

from agents.reseaux_sociaux.brief import PostBrief

_MODEL = "claude-sonnet-5"

_SYSTEM_PROMPT = """Tu rédiges une publication pour les réseaux sociaux (Facebook/Instagram) \
d'une PME ou d'un indépendant en Afrique (Gabon). Ton chaleureux, clair et professionnel, en \
français. Réponds uniquement avec un objet JSON valide, sans texte autour, respectant \
exactement ce schéma :

{
  "caption": "texte de la publication (3 à 6 phrases, adapté à Facebook/Instagram)",
  "hashtags": ["motcle1", "motcle2"]
}

Prévois entre 2 et 5 hashtags pertinents, en minuscules, sans le caractère "#". Les éléments \
listés comme obligatoires par le client doivent apparaître fidèlement dans le texte, sans \
les inventer ni les modifier. N'ajoute aucune information (prix, date, offre) qui ne t'a pas \
été fournie explicitement."""


class PostContent(BaseModel):
    caption: str
    hashtags: list[str] = []


class ContentGenerationError(RuntimeError):
    """Levée quand la réponse de Claude ne peut pas être interprétée comme du PostContent."""


def generate_content(
    brief: PostBrief, brand_voice: str | None, *, client: anthropic.Anthropic | None = None
) -> PostContent:
    client = client or anthropic.Anthropic()

    mandatory = "\n".join(f"- {element}" for element in brief.mandatory_elements) or "(aucun)"
    user_message = (
        f"Objectif de la publication : {brief.objective.value}\n"
        f"Ton/voix de la marque : {brand_voice or 'ton neutre et professionnel par défaut'}\n"
        f"Éléments obligatoires à inclure fidèlement :\n{mandatory}"
    )

    response = client.messages.create(
        model=_MODEL,
        max_tokens=1000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")

    try:
        payload = json.loads(text)
        return PostContent.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ContentGenerationError(
            f"Réponse de Claude non conforme au schéma PostContent : {exc}\nRéponse brute : {text}"
        ) from exc
