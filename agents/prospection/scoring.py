"""Scoring pondéré et auditable des prospects (agents/prospection/skills/README.md).

Fonction pure, sans I/O : les poids et seuils sont des paramètres explicites (pas codés en
dur au cœur de la logique), pour rester ajustables par l'équipe commerciale sans toucher au
code — exigence déjà actée dans le skills/README.md.
"""

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel

from platform_core.models import ProspectCategory


class WebsiteStatus(str, Enum):
    none = "none"
    outdated = "outdated"
    modern = "modern"


class ProspectSignals(BaseModel):
    """Signaux collectés sur un prospect, entrée du scoring."""

    has_valid_contact: bool
    website_status: WebsiteStatus
    sector_matches_catalog: bool
    has_recent_activity_signal: bool


@dataclass
class ScoringWeights:
    website_none_or_outdated: int = 3
    website_modern: int = -3
    sector_matches_catalog: int = 2
    recent_activity_signal: int = 1
    favorable_threshold: int = 3
    non_favorable_threshold: int = -1


def score_prospect(
    signals: ProspectSignals, *, weights: ScoringWeights | None = None
) -> tuple[ProspectCategory, int]:
    """Retourne (catégorie, score). Coordonnées invalides -> "non joignable" immédiat, sans
    calcul de score (agents/prospection/skills/README.md : "exclusion immédiate")."""
    if not signals.has_valid_contact:
        return ProspectCategory.non_joignable, 0

    weights = weights or ScoringWeights()
    score = 0

    if signals.website_status in (WebsiteStatus.none, WebsiteStatus.outdated):
        score += weights.website_none_or_outdated
    elif signals.website_status == WebsiteStatus.modern:
        score += weights.website_modern

    if signals.sector_matches_catalog:
        score += weights.sector_matches_catalog

    if signals.has_recent_activity_signal:
        score += weights.recent_activity_signal
    # Absence de signal d'activité : ni bonus ni malus explicite — l'absence de donnée
    # pousse vers "à qualifier" via les seuils plutôt que vers un rejet (skills/README.md).

    if score >= weights.favorable_threshold:
        category = ProspectCategory.favorable
    elif score <= weights.non_favorable_threshold:
        category = ProspectCategory.non_favorable
    else:
        category = ProspectCategory.a_qualifier

    return category, score
