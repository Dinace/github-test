"""Vue d'ensemble transverse de l'activité d'un client à travers les 4 autres agents.

Lecture seule : agrège les tables déjà possédées par chaque agent (Site, Post, Prospect),
ne les modifie jamais — Planning ne fait qu'observer, jamais écrire dans le périmètre d'un
autre agent (cloisonnement strict, CLAUDE.md §5).
"""

import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from platform_core.models import ContactStatus, Post, PostStatus, Prospect, ProspectCategory, Site, SiteStatus


class ClientActivitySummary(BaseModel):
    sites_awaiting_validation: int
    posts_awaiting_validation: int
    prospects_to_qualify: int
    prospects_awaiting_contact_validation: int


def get_client_activity_summary(client_id: uuid.UUID, *, db: Session) -> ClientActivitySummary:
    sites_awaiting = (
        db.query(Site)
        .filter(Site.client_id == client_id, Site.status == SiteStatus.draft, Site.content.isnot(None))
        .count()
    )
    posts_awaiting = (
        db.query(Post).filter(Post.client_id == client_id, Post.status == PostStatus.pending_validation).count()
    )
    prospects_to_qualify = (
        db.query(Prospect)
        .filter(Prospect.client_id == client_id, Prospect.category == ProspectCategory.a_qualifier)
        .count()
    )
    prospects_awaiting_contact = (
        db.query(Prospect)
        .filter(Prospect.client_id == client_id, Prospect.contact_status == ContactStatus.pending_validation)
        .count()
    )

    return ClientActivitySummary(
        sites_awaiting_validation=sites_awaiting,
        posts_awaiting_validation=posts_awaiting,
        prospects_to_qualify=prospects_to_qualify,
        prospects_awaiting_contact_validation=prospects_awaiting_contact,
    )
