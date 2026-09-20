"""Génération du contenu textuel d'un site à partir d'un brief.

Choix délibéré : un appel direct à l'API Claude (Messages API), pas le Claude Agent SDK.
Cette tâche est une génération structurée en un seul appel (brief -> JSON de contenu), pas
une exploration ouverte à plusieurs étapes ; le harnais complet du Agent SDK (accès
Bash/fichiers, boucle autonome) n'a pas d'utilité ici et élargirait inutilement le périmètre
de cet agent (CLAUDE.md §5 : cloisonnement strict). Modèle Sonnet 5 : choix de coût déjà
validé dans docs/pricing-model.md pour cette action.
"""

import json

import anthropic
from pydantic import BaseModel, ValidationError

from agents.creation_site.brief import Sector, SiteBrief

_SECTOR_LABELS: dict[Sector, str] = {
    Sector.restaurant: "restaurant ou restauration rapide",
    Sector.boutique: "boutique ou commerce de détail",
    Sector.beaute_bien_etre: "services de beauté et bien-être",
    Sector.artisanat: "artisanat ou métier technique",
    Sector.services_professionnels: "services professionnels ou de conseil",
    Sector.sante: "établissement de santé",
    Sector.hotellerie_tourisme: "hôtellerie ou tourisme",
    Sector.education_formation: "éducation ou formation",
    Sector.evenementiel: "événementiel",
    Sector.generique: "activité générale",
}

_MODEL = "claude-sonnet-5"

_SYSTEM_PROMPT = """Tu rédiges le contenu textuel d'un site vitrine pour une PME ou un \
indépendant en Afrique (Gabon). Le ton doit être clair, chaleureux et professionnel, en \
français. Réponds uniquement avec un objet JSON valide, sans texte autour, respectant \
exactement ce schéma :

{
  "hero_tagline": "accroche courte (moins de 10 mots)",
  "hero_subtitle": "une phrase complétant l'accroche",
  "about_text": "un paragraphe de présentation de l'activité (3-5 phrases)",
  "items": [
    {"title": "...", "description": "..."}
  ],
  "contact_intro": "une phrase courte introduisant la section contact"
}

"items" représente les éléments clés à mettre en avant selon le secteur (plats du menu, \
produits, prestations, réalisations, chambres, programmes... adapte au secteur donné).
Prévois entre 3 et 6 éléments dans "items". N'invente pas de prix ni de coordonnées précises \
qui ne figurent pas dans la description fournie par le client.

Si le secteur est "établissement de santé" : ne génère aucun contenu médical (diagnostic, \
traitement, conseil de santé) — reste sur la présentation générale de l'établissement et de \
ses spécialités déclarées, un professionnel de santé doit valider tout contenu médical \
avant publication (règle non négociable)."""


class ContentItem(BaseModel):
    title: str
    description: str


class SiteContent(BaseModel):
    hero_tagline: str
    hero_subtitle: str
    about_text: str
    items: list[ContentItem]
    contact_intro: str


class ContentGenerationError(RuntimeError):
    """Levée quand la réponse de Claude ne peut pas être interprétée comme du SiteContent."""


def generate_content(brief: SiteBrief, *, client: anthropic.Anthropic | None = None) -> SiteContent:
    client = client or anthropic.Anthropic()

    user_message = (
        f"Nom de l'activité : {brief.business_name}\n"
        f"Secteur : {_SECTOR_LABELS[brief.sector]}\n"
        f"Description fournie par le client : {brief.description}"
    )

    response = client.messages.create(
        model=_MODEL,
        max_tokens=2000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")

    try:
        payload = json.loads(text)
        return SiteContent.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ContentGenerationError(
            f"Réponse de Claude non conforme au schéma SiteContent : {exc}\nRéponse brute : {text}"
        ) from exc
