"""Collecte sécurisée des accès réseaux du client (Meta, WhatsApp Business) — "office
manager" (extension de Planning, décision actée avec l'utilisateur, voir MEMORY.md).

Écrit dans des champs déjà existants sur `platform_core.models.Client`
(`meta_page_id`/`meta_page_access_token`, `whatsapp_phone_number_id`/`whatsapp_access_token`),
chiffrés au repos (`EncryptedString`, voir `platform_core/encryption.py`) — jusqu'ici
renseignés uniquement à la main en base (agents/reseaux_sociaux/skills/README.md,
agents/prospection/skills/README.md), sans point de collecte applicatif. Ce module en est le
premier. Écrire dans `Client` (modèle **partagé**, pas "possédé" par Réseaux sociaux ou
Prospection) reste cohérent avec le cloisonnement (CLAUDE.md §5) : Planning ne modifie
jamais le périmètre PROPRE d'un autre agent (Site, Post, Prospect...), et ces deux champs
sont déjà pensés comme des identifiants client génériques réutilisables par plusieurs agents.

Sécurité : ces fonctions ne retournent JAMAIS la valeur en clair d'un token, seulement des
indicateurs booléens de présence — une fois soumis via `set_network_access`, un token reste
utilisable par les agents concernés (Réseaux sociaux, Prospection) mais n'est plus jamais
relisible via l'API (write-only, comme une clé API client — voir platform_core/auth.py pour
le même principe appliqué à `Client.api_key_hash`).
"""

import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from platform_core.models import Client


class ClientNotFoundError(RuntimeError):
    pass


class NetworkAccessUpdate(BaseModel):
    """Mise à jour partielle : seuls les champs fournis (non `None`) sont écrits — soumettre
    un seul champ (ex. un nouveau token après rotation) ne doit jamais effacer les autres."""

    meta_page_id: str | None = None
    meta_page_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_access_token: str | None = None


class NetworkAccessStatus(BaseModel):
    client_id: uuid.UUID
    meta_connected: bool
    whatsapp_connected: bool


def _status(client: Client) -> NetworkAccessStatus:
    return NetworkAccessStatus(
        client_id=client.id,
        meta_connected=bool(client.meta_page_id and client.meta_page_access_token),
        whatsapp_connected=bool(client.whatsapp_phone_number_id and client.whatsapp_access_token),
    )


def _get_client(client_id: uuid.UUID, *, db: Session) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise ClientNotFoundError(f"Client introuvable : {client_id}")
    return client


def get_network_access_status(client_id: uuid.UUID, *, db: Session) -> NetworkAccessStatus:
    return _status(_get_client(client_id, db=db))


def set_network_access(client_id: uuid.UUID, update: NetworkAccessUpdate, *, db: Session) -> NetworkAccessStatus:
    client = _get_client(client_id, db=db)

    if update.meta_page_id is not None:
        client.meta_page_id = update.meta_page_id
    if update.meta_page_access_token is not None:
        client.meta_page_access_token = update.meta_page_access_token
    if update.whatsapp_phone_number_id is not None:
        client.whatsapp_phone_number_id = update.whatsapp_phone_number_id
    if update.whatsapp_access_token is not None:
        client.whatsapp_access_token = update.whatsapp_access_token

    db.commit()
    db.refresh(client)
    return _status(client)
