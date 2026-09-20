from enum import Enum

from pydantic import BaseModel, Field


class Sector(str, Enum):
    """Catalogue de secteurs (agents/creation_site/skills/README.md)."""

    restaurant = "restaurant"
    boutique = "boutique"
    beaute_bien_etre = "beaute_bien_etre"
    artisanat = "artisanat"
    services_professionnels = "services_professionnels"
    sante = "sante"
    hotellerie_tourisme = "hotellerie_tourisme"
    education_formation = "education_formation"
    evenementiel = "evenementiel"
    generique = "generique"


class SiteBrief(BaseModel):
    """Brief client saisi via le dashboard, point de départ de la génération de site."""

    business_name: str
    sector: Sector
    description: str = Field(
        description="Description libre de l'activité fournie par le client, "
        "utilisée comme matière première pour la génération de contenu."
    )
    phone: str
    whatsapp: str | None = None
    address: str | None = None
