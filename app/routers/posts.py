import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.reseaux_sociaux import agent as post_agent
from agents.reseaux_sociaux import meta
from agents.reseaux_sociaux.brief import PostBrief
from agents.reseaux_sociaux.content import ContentGenerationError, PostContent
from app.auth import get_current_client
from platform_core.activity import log_event
from platform_core.db import get_db
from platform_core.models import Client, Post, PostStatus

router = APIRouter(prefix="/api/posts", tags=["posts"])


class ScheduleRequest(BaseModel):
    scheduled_at: datetime | None = None


def _get_owned_post(post_id: uuid.UUID, current_client: Client, db: Session) -> Post:
    """Charge la publication et vérifie qu'elle appartient bien au client authentifié
    (même principe de cloisonnement que app.routers.sites._get_owned_site)."""
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Publication introuvable")
    if post.client_id != current_client.id:
        raise HTTPException(status_code=403, detail="Cette publication n'appartient pas au client authentifié")
    return post


def _require_status(post: Post, expected: PostStatus) -> None:
    if post.status != expected:
        raise HTTPException(
            status_code=409,
            detail=f"Action impossible : statut actuel '{post.status.value}', attendu '{expected.value}'",
        )


@router.post("", status_code=201)
def create_post(
    brief: PostBrief,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> dict:
    post = Post(client_id=current_client.id, brief=brief.model_dump(mode="json"))
    db.add(post)
    db.commit()
    db.refresh(post)
    log_event(
        db,
        client_id=current_client.id,
        agent="reseaux_sociaux",
        entity_type="post",
        entity_id=post.id,
        event_type="created",
    )
    return {"id": str(post.id), "status": post.status.value}


@router.post("/{post_id}/generate")
def generate_post(
    post_id: uuid.UUID,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> dict:
    post = _get_owned_post(post_id, current_client, db)
    _require_status(post, PostStatus.draft)

    brief = PostBrief.model_validate(post.brief)
    try:
        content: PostContent = post_agent.generate_draft_content(brief, current_client.brand_voice)
    except ContentGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    post.content = content.model_dump(mode="json")
    post.status = PostStatus.pending_validation
    db.commit()
    log_event(
        db,
        client_id=current_client.id,
        agent="reseaux_sociaux",
        entity_type="post",
        entity_id=post.id,
        event_type="content_generated",
    )
    return {"id": str(post.id), "status": post.status.value}


@router.post("/{post_id}/request-changes")
def request_changes(
    post_id: uuid.UUID,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> dict:
    post = _get_owned_post(post_id, current_client, db)
    _require_status(post, PostStatus.pending_validation)

    # Retour à brouillon : le contenu sera régénéré, pas conservé tel quel (agents/
    # reseaux_sociaux/skills/README.md, workflow de validation).
    post.content = None
    post.status = PostStatus.draft
    db.commit()
    log_event(
        db,
        client_id=current_client.id,
        agent="reseaux_sociaux",
        entity_type="post",
        entity_id=post.id,
        event_type="changes_requested",
    )
    return {"id": str(post.id), "status": post.status.value}


@router.post("/{post_id}/validate")
def validate_post(
    post_id: uuid.UUID,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> dict:
    post = _get_owned_post(post_id, current_client, db)
    _require_status(post, PostStatus.pending_validation)

    post.status = PostStatus.validated
    db.commit()
    log_event(
        db,
        client_id=current_client.id,
        agent="reseaux_sociaux",
        entity_type="post",
        entity_id=post.id,
        event_type="validated",
    )
    return {"id": str(post.id), "status": post.status.value}


@router.post("/{post_id}/schedule")
def schedule_post(
    post_id: uuid.UUID,
    payload: ScheduleRequest,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> dict:
    post = _get_owned_post(post_id, current_client, db)
    _require_status(post, PostStatus.validated)

    brief = PostBrief.model_validate(post.brief)
    scheduled_at = payload.scheduled_at or brief.requested_publish_at
    if scheduled_at is None:
        raise HTTPException(
            status_code=422,
            detail="Aucune date de publication : à fournir ici ou dans le brief (requested_publish_at)",
        )

    post.scheduled_at = scheduled_at
    post.status = PostStatus.scheduled
    db.commit()
    log_event(
        db,
        client_id=current_client.id,
        agent="reseaux_sociaux",
        entity_type="post",
        entity_id=post.id,
        event_type="scheduled",
        details={"scheduled_at": scheduled_at.isoformat()},
    )
    return {"id": str(post.id), "status": post.status.value, "scheduled_at": scheduled_at.isoformat()}


@router.post("/{post_id}/publish")
def publish_post(
    post_id: uuid.UUID,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> dict:
    post = _get_owned_post(post_id, current_client, db)
    _require_status(post, PostStatus.scheduled)

    try:
        post_agent.publish_scheduled_post(post, current_client)
    except post_agent.MissingMetaConnectionError as exc:
        raise HTTPException(status_code=412, detail=str(exc)) from exc
    except meta.MetaPublishError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    post.status = PostStatus.published
    post.published_at = datetime.now(UTC)
    db.commit()
    log_event(
        db,
        client_id=current_client.id,
        agent="reseaux_sociaux",
        entity_type="post",
        entity_id=post.id,
        event_type="published",
    )
    return {"id": str(post.id), "status": post.status.value}
