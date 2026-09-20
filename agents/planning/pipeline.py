"""Historique du pipeline d'un prospect dans le temps (platform_core.activity).

Complète le statut ponctuel déjà géré par l'agent Prospection (Prospect.category/
contact_status, qui ne retiennent que l'état courant) avec une vue chronologique.
"""

import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from platform_core.models import ActivityEvent


class PipelineEvent(BaseModel):
    event_type: str
    occurred_at: str
    details: dict


def get_prospect_pipeline(prospect_id: uuid.UUID, *, db: Session) -> list[PipelineEvent]:
    events = (
        db.query(ActivityEvent)
        .filter(ActivityEvent.entity_type == "prospect", ActivityEvent.entity_id == prospect_id)
        .order_by(ActivityEvent.occurred_at)
        .all()
    )
    return [
        PipelineEvent(event_type=e.event_type, occurred_at=e.occurred_at.isoformat(), details=e.details)
        for e in events
    ]
