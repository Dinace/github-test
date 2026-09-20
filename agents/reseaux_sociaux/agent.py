"""Point d'entrée de l'agent Réseaux sociaux : brief -> contenu généré -> publication."""

import anthropic

from agents.reseaux_sociaux import meta
from agents.reseaux_sociaux.brief import PostBrief
from agents.reseaux_sociaux.content import PostContent, generate_content
from platform_core.models import Client, Post


def generate_draft_content(
    brief: PostBrief, brand_voice: str | None, *, client: anthropic.Anthropic | None = None
) -> PostContent:
    """Génère le contenu texte de la publication. Le contenu est la source de vérité,
    stocké en base (platform_core.models.Post.content) — pas d'artefact dérivé à écrire
    ailleurs, contrairement à l'agent Création de site (pas de rendu/stockage de fichier)."""
    return generate_content(brief, brand_voice, client=client)


class MissingMetaConnectionError(RuntimeError):
    """Levée quand le client n'a pas connecté sa Page Meta (meta_page_id/access_token)."""


def publish_scheduled_post(post: Post, client: Client) -> str:
    """Publie un post `scheduled` sur la Page Meta du client. Factorisé hors de
    `app/routers/posts.py` pour être appelé aussi bien par l'endpoint manuel
    `POST /api/posts/{id}/publish` que par la tâche planifiée
    (`agents/reseaux_sociaux/scheduled_jobs.py::publish_due_posts`) sans dupliquer la
    logique de construction du message. Ne change pas le statut du post ni ne commit en
    base : ça reste la responsabilité de l'appelant (statuts/erreurs gérés différemment
    selon le contexte HTTP vs planifié)."""
    if not client.meta_page_id or not client.meta_page_access_token:
        raise MissingMetaConnectionError(
            "Aucune Page Meta connectée pour ce client (meta_page_id/meta_page_access_token manquants)"
        )

    content = PostContent.model_validate(post.content)
    hashtags = " ".join(f"#{tag}" for tag in content.hashtags)
    message = f"{content.caption}\n\n{hashtags}".strip()
    return meta.publish_to_meta(client.meta_page_id, client.meta_page_access_token, message)
