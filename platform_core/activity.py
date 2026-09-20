"""Journalisation d'événements d'activité, partagée entre agents.

Vit dans platform_core (pas dans un agent précis) car plusieurs agents y écrivent — voir
platform_core.models.ActivityEvent pour la justification de ce choix vis-à-vis du
cloisonnement (CLAUDE.md §5). Chaque appelant ne journalise que SES PROPRES actions.
"""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from platform_core.models import ActivityEvent


def log_event(
    db: Session,
    *,
    client_id: uuid.UUID,
    agent: str,
    entity_type: str,
    entity_id: uuid.UUID,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> ActivityEvent:
    event = ActivityEvent(
        client_id=client_id,
        agent=agent,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        details=details or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
