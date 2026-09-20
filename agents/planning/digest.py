"""Synthèse en langage naturel de l'activité d'un client, pour l'équipe.

Même choix que les 4 autres agents (agents/creation_site/skills/README.md) : appel direct à
l'API Claude, pas le Claude Agent SDK — transformer des compteurs structurés en une phrase
de synthèse est un appel unique, pas une tâche agentique ouverte.
"""

import anthropic

from agents.planning.dashboard import ClientActivitySummary

_MODEL = "claude-sonnet-5"

_SYSTEM_PROMPT = """Tu rédiges une courte synthèse (2 à 3 phrases) à l'attention de l'équipe \
qui gère une plateforme de digitalisation pour PME, à partir de compteurs d'activité d'un \
client. Ton neutre et factuel, en français. Réponds uniquement avec le texte de la \
synthèse, sans JSON ni formatage."""


def generate_digest(summary: ClientActivitySummary, *, client: anthropic.Anthropic | None = None) -> str:
    client = client or anthropic.Anthropic()

    user_message = (
        f"Sites en attente de validation : {summary.sites_awaiting_validation}\n"
        f"Publications en attente de validation : {summary.posts_awaiting_validation}\n"
        f"Prospects à qualifier : {summary.prospects_to_qualify}\n"
        f"Prospects en attente de validation de contact : {summary.prospects_awaiting_contact_validation}"
    )

    response = client.messages.create(
        model=_MODEL,
        max_tokens=300,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
