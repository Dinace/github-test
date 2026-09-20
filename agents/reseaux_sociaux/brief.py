from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PostObjective(str, Enum):
    """Catalogue d'objectifs (agents/reseaux_sociaux/skills/README.md)."""

    promotion = "promotion"
    annonce = "annonce"
    engagement = "engagement"


class PostBrief(BaseModel):
    """Brief client saisi via le dashboard pour une publication réseaux sociaux."""

    objective: PostObjective
    mandatory_elements: list[str] = Field(
        default_factory=list,
        description="Éléments qui doivent apparaître fidèlement dans le texte (prix, "
        "date, offre, mention légale...) — jamais inventés par l'agent.",
    )
    requested_publish_at: datetime | None = None
    visual_provided_by_client: bool = False
