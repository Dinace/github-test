"""Structuration de fiche prospect et génération du message de premier contact.

Même choix que les 3 autres agents (agents/creation_site/skills/README.md) : appel direct à
l'API Claude, pas le Claude Agent SDK — ce sont des générations structurées en un seul
appel, pas des tâches agentiques ouvertes.
"""

import json

import anthropic
from pydantic import BaseModel, ValidationError

_MODEL = "claude-sonnet-5"

_STRUCTURE_SYSTEM_PROMPT = """Tu structures les données brutes d'un établissement collectées \
sur un support public (annuaire, page professionnelle) en une fiche prospect. Réponds \
uniquement avec un objet JSON valide, sans texte autour, respectant exactement ce schéma :

{
  "business_name": "nom de l'établissement",
  "sector": "secteur d'activité en quelques mots",
  "likely_needs": "un court paragraphe sur les besoins probables de digitalisation, à partir des seules données fournies"
}

N'invente aucune information qui ne figure pas dans le texte fourni."""

_CONTACT_SYSTEM_PROMPT = """Tu rédiges un premier message de contact WhatsApp, chaleureux et \
professionnel, en français, pour présenter brièvement une offre de digitalisation à un \
prospect (PME ou indépendant en Afrique). Réponds uniquement avec un objet JSON valide, sans \
texte autour, respectant exactement ce schéma :

{
  "message": "texte du message (3-5 phrases maximum, ton WhatsApp, pas un email formel)"
}

Ne mentionne aucun prix ni engagement ferme. N'invente aucune information sur le prospect \
au-delà de ce qui est fourni."""


class ProspectCard(BaseModel):
    business_name: str
    sector: str
    likely_needs: str


class ContactMessage(BaseModel):
    message: str


class ContentGenerationError(RuntimeError):
    """Levée quand la réponse de Claude ne peut pas être interprétée comme attendu."""


def _call_claude(system_prompt: str, user_message: str, client: anthropic.Anthropic | None) -> str:
    client = client or anthropic.Anthropic()
    response = client.messages.create(
        model=_MODEL,
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def structure_prospect(raw_text: str, *, client: anthropic.Anthropic | None = None) -> ProspectCard:
    text = _call_claude(_STRUCTURE_SYSTEM_PROMPT, raw_text, client)
    try:
        return ProspectCard.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ContentGenerationError(
            f"Réponse de Claude non conforme au schéma ProspectCard : {exc}\nRéponse brute : {text}"
        ) from exc


def generate_contact_message(
    business_name: str, sector: str, likely_needs: str, brand_voice: str | None, *, client: anthropic.Anthropic | None = None
) -> ContactMessage:
    user_message = (
        f"Prospect : {business_name}\n"
        f"Secteur : {sector}\n"
        f"Besoins probables : {likely_needs}\n"
        f"Ton de l'entreprise qui contacte : {brand_voice or 'ton neutre et professionnel par défaut'}"
    )
    text = _call_claude(_CONTACT_SYSTEM_PROMPT, user_message, client)
    try:
        return ContactMessage.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ContentGenerationError(
            f"Réponse de Claude non conforme au schéma ContactMessage : {exc}\nRéponse brute : {text}"
        ) from exc
