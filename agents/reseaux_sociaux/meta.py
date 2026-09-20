"""Publication réelle sur Meta Graph API (post texte sur une Page Facebook/Instagram).

Portée volontairement limitée : WhatsApp Business n'a pas d'équivalent "publication" au sens
réseau social — c'est un canal de messagerie directe basé sur l'opt-in et des templates
approuvés par Meta, un flux différent et plus lourd (gestion des opt-in, approbation des
templates) que la publication d'un post. Volontairement pas implémenté ici plutôt que fait à
moitié — voir "points ouverts" dans agents/reseaux_sociaux/skills/README.md.

Nécessite que le client ait connecté sa Page Facebook/Instagram (`Client.meta_page_id` +
`Client.meta_page_access_token`). Le flux OAuth de connexion (Facebook Login, sélection de
page, échange de token longue durée) n'est pas implémenté : ces deux champs doivent être
renseignés manuellement en attendant.
"""

import httpx

_GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class MetaPublishError(RuntimeError):
    """Levée quand l'appel à l'API Meta échoue (HTTP >= 400)."""


def publish_to_meta(
    page_id: str, access_token: str, message: str, *, http_client: httpx.Client | None = None
) -> str:
    """Publie un post texte sur la Page Meta. Retourne l'identifiant du post créé."""
    client = http_client or httpx.Client()
    response = client.post(
        f"{_GRAPH_API_BASE}/{page_id}/feed",
        data={"message": message, "access_token": access_token},
    )
    if response.status_code >= 400:
        raise MetaPublishError(f"Échec de publication Meta ({response.status_code}) : {response.text}")

    return response.json()["id"]
