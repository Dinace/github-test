"""Envoi réel du premier message de contact via WhatsApp Business Cloud API.

Nécessite que le client ait connecté son numéro WhatsApp Business
(`Client.whatsapp_phone_number_id` + `whatsapp_access_token`). Même limite que
`agents/reseaux_sociaux/meta.py` : pas de flux de connexion automatisé, credentials
renseignés manuellement en attendant.
"""

import httpx

_GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class WhatsAppSendError(RuntimeError):
    """Levée quand l'appel à l'API WhatsApp échoue (HTTP >= 400)."""


def send_whatsapp_message(
    phone_number_id: str, access_token: str, to: str, message: str, *, http_client: httpx.Client | None = None
) -> str:
    """Envoie un message texte. Retourne l'identifiant du message envoyé."""
    client = http_client or httpx.Client()
    response = client.post(
        f"{_GRAPH_API_BASE}/{phone_number_id}/messages",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message},
        },
    )
    if response.status_code >= 400:
        raise WhatsAppSendError(f"Échec d'envoi WhatsApp ({response.status_code}) : {response.text}")

    return response.json()["messages"][0]["id"]
