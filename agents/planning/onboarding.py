"""Suivi des étapes de mise en place de l'offre chez un client ("office manager").

Décision actée avec l'utilisateur : ce n'est pas un agent séparé mais une extension de
l'agent Planning (voir MEMORY.md, agents/planning/skills/README.md) — Planning fait déjà du
suivi transverse de l'activité client (dashboard.py), ce module en est la déclinaison
"étapes d'implémentation" plutôt que "actions en attente de validation".

Chaque étape est **calculée** à partir des données déjà possédées par les autres agents
(Site, Post, Prospect, Backup, Subscription) — même principe que
dashboard.py::get_client_activity_summary : Planning observe, ne duplique jamais un état déjà
suivi ailleurs, et n'écrit jamais dans le périmètre d'un autre agent (CLAUDE.md §5).
"""

import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from platform_core.models import (
    Backup,
    Pack,
    Post,
    PostStatus,
    Prospect,
    Site,
    SiteStatus,
    Subscription,
)


class OnboardingStep(BaseModel):
    key: str
    label: str
    done: bool
    # "commercial" | "technique" — équipe interne à notifier quand l'étape est franchie
    # (voir agents/planning/scheduled_jobs.py::notify_onboarding_progress).
    team: str


def _active_pack(client_id: uuid.UUID, *, db: Session) -> Pack:
    subscription = (
        db.query(Subscription).filter(Subscription.client_id == client_id, Subscription.active.is_(True)).first()
    )
    return subscription.pack if subscription is not None else Pack.starter


def get_onboarding_checklist(client_id: uuid.UUID, *, db: Session) -> list[OnboardingStep]:
    """Retourne la liste des étapes attendues pour ce client, dans l'ordre. Les étapes
    Réseaux sociaux/Prospection n'apparaissent que pour les packs qui les incluent
    (CLAUDE.md §1 : absents du Starter) — inutile de notifier le commercial d'une étape que
    ce client n'a pas achetée."""
    pack = _active_pack(client_id, db=db)

    site = db.query(Site).filter(Site.client_id == client_id).order_by(Site.created_at).first()
    steps = [
        OnboardingStep(key="site_created", label="Site créé (brief renseigné)", done=site is not None, team="commercial"),
        OnboardingStep(
            key="site_content_generated",
            label="Contenu du site généré",
            done=bool(site and site.content is not None),
            team="commercial",
        ),
        OnboardingStep(
            key="site_published",
            label="Site publié",
            done=bool(site and site.status == SiteStatus.published),
            team="commercial",
        ),
    ]

    # Sauvegarde plateforme, pas par client (voir platform_core.models.Backup) : dès qu'une
    # sauvegarde existe, les données de CE client en font partie — l'étape est donc partagée
    # par tous les clients, cohérent avec le choix déjà acté pour la cadence de sauvegarde
    # (agents/maintenance/scheduled_jobs.py).
    has_backup = db.query(Backup).first() is not None
    steps.append(
        OnboardingStep(key="first_backup_confirmed", label="Première sauvegarde confirmée", done=has_backup, team="technique")
    )

    if pack in (Pack.business, Pack.premium):
        first_post_published = (
            db.query(Post).filter(Post.client_id == client_id, Post.status == PostStatus.published).first() is not None
        )
        steps.append(
            OnboardingStep(
                key="social_media_active",
                label="Première publication réseaux sociaux réalisée",
                done=first_post_published,
                team="commercial",
            )
        )

        has_prospects = db.query(Prospect).filter(Prospect.client_id == client_id).first() is not None
        steps.append(
            OnboardingStep(
                key="prospection_started", label="Prospection commerciale démarrée", done=has_prospects, team="commercial"
            )
        )

    return steps
