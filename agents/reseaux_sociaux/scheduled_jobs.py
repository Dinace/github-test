"""Tâche planifiée : auto-publication des posts programmés (`Post.status == scheduled` et
`Post.scheduled_at` échu). Comblait le point ouvert "rien ne déclenche encore `publish`
automatiquement à cette date" (agents/reseaux_sociaux/skills/README.md) — enregistrée dans
`platform_core/scheduler.py`.
"""

from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from agents.reseaux_sociaux import agent as post_agent
from agents.reseaux_sociaux import meta
from platform_core.models import (
    Client,
    Notification,
    NotificationCategory,
    NotificationSeverity,
    NotificationStatus,
    Post,
    PostStatus,
)


def publish_due_posts(session_factory: Callable[[], AbstractContextManager[Session]]) -> None:
    with session_factory() as db:
        now = datetime.now(UTC)
        due_posts = (
            db.query(Post)
            .filter(Post.status == PostStatus.scheduled, Post.scheduled_at.isnot(None), Post.scheduled_at <= now)
            .all()
        )

        for post in due_posts:
            client = db.get(Client, post.client_id)
            try:
                post_agent.publish_scheduled_post(post, client)
            except (post_agent.MissingMetaConnectionError, meta.MetaPublishError) as exc:
                # Notifie le staff plutôt que de réessayer indéfiniment en silence à chaque
                # tick : une connexion Meta manquante ou un rejet de l'API ne se résout pas
                # tout seul, un humain doit intervenir (reconnecter la Page, corriger le
                # contenu...). Le post reste "scheduled" et sera retenté au prochain tick
                # (5 minutes) tant que le problème n'est pas résolu ; on évite une
                # notification en double tant que la précédente n'a pas été acquittée
                # (recherchée par l'id du post dans le message, pas de champ dédié).
                already_notified = (
                    db.query(Notification)
                    .filter(
                        Notification.client_id == client.id,
                        Notification.category == NotificationCategory.error_spike,
                        Notification.status == NotificationStatus.pending,
                        Notification.message.contains(str(post.id)),
                    )
                    .first()
                )
                if already_notified is None:
                    db.add(
                        Notification(
                            category=NotificationCategory.error_spike,
                            severity=NotificationSeverity.warning,
                            message=(
                                f"Échec de la publication automatique programmée du post {post.id} "
                                f"(client {client.name}) : {exc}"
                            ),
                            client_id=client.id,
                        )
                    )
                continue

            post.status = PostStatus.published
            post.published_at = now

        db.commit()
