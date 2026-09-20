import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.maintenance import backup as backup_module
from agents.maintenance import restore as restore_module
from app.auth import require_ops_token
from platform_core.db import get_db
from platform_core.models import Backup, Notification, NotificationCategory, NotificationSeverity, NotificationStatus

router = APIRouter(
    prefix="/api/maintenance",
    tags=["maintenance"],
    dependencies=[Depends(require_ops_token)],
)


class AcknowledgeRequest(BaseModel):
    acknowledged_by: str


class RestoreProposalRequest(BaseModel):
    reason: str


class ConfirmRestoreRequest(BaseModel):
    confirmed_by: str


@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db)) -> list[dict]:
    notifications = (
        db.query(Notification).filter(Notification.status == NotificationStatus.pending).order_by(Notification.created_at).all()
    )
    return [
        {
            "id": str(n.id),
            "category": n.category.value,
            "severity": n.severity.value,
            "message": n.message,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]


@router.post("/notifications/{notification_id}/acknowledge")
def acknowledge_notification(
    notification_id: uuid.UUID, payload: AcknowledgeRequest, db: Session = Depends(get_db)
) -> dict:
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification introuvable")

    notification.status = NotificationStatus.acknowledged
    notification.acknowledged_by = payload.acknowledged_by
    notification.acknowledged_at = datetime.now(UTC)
    db.commit()
    return {"id": str(notification.id), "status": notification.status.value}


@router.post("/backups", status_code=201)
def trigger_backup(db: Session = Depends(get_db)) -> dict:
    """Déclenche une sauvegarde immédiate (pg_dump + upload R2).

    Pas de vraie tâche planifiée pour l'instant (voir agents/maintenance/skills/
    README.md, "points ouverts") — appel manuel en attendant.
    """
    try:
        dump = backup_module.create_backup()
        timestamp = datetime.now(UTC)
        key = backup_module.upload_backup(dump, timestamp)
    except Exception as exc:  # noqa: BLE001 — toute panne de backup doit notifier, jamais échouer en silence
        notification = Notification(
            category=NotificationCategory.backup_failure,
            severity=NotificationSeverity.critical,
            message=f"Échec de la sauvegarde planifiée : {exc}",
        )
        db.add(notification)
        db.commit()
        raise HTTPException(status_code=502, detail=f"Échec de la sauvegarde : {exc}") from exc

    record = Backup(r2_key=key, size_bytes=len(dump))
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": str(record.id), "r2_key": record.r2_key, "size_bytes": record.size_bytes}


@router.get("/backups")
def list_backups(db: Session = Depends(get_db)) -> list[dict]:
    backups = db.query(Backup).order_by(Backup.created_at.desc()).all()
    return [
        {"id": str(b.id), "r2_key": b.r2_key, "size_bytes": b.size_bytes, "created_at": b.created_at.isoformat()}
        for b in backups
    ]


@router.post("/backups/{backup_id}/restore-requests", status_code=201)
def propose_restore(backup_id: uuid.UUID, payload: RestoreProposalRequest, db: Session = Depends(get_db)) -> dict:
    if db.get(Backup, backup_id) is None:
        raise HTTPException(status_code=404, detail="Sauvegarde introuvable")

    request = restore_module.propose_restore(backup_id, payload.reason, db=db)
    return {"id": str(request.id), "status": request.status.value}


@router.post("/restore-requests/{restore_request_id}/confirm")
def confirm_restore(restore_request_id: uuid.UUID, payload: ConfirmRestoreRequest, db: Session = Depends(get_db)) -> dict:
    try:
        request = restore_module.confirm_restore(restore_request_id, payload.confirmed_by, db=db)
    except restore_module.RestoreRequestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"id": str(request.id), "status": request.status.value}


@router.post("/restore-requests/{restore_request_id}/execute")
def execute_restore(restore_request_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    try:
        request = restore_module.execute_restore(restore_request_id, db=db)
    except restore_module.RestoreRequestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except restore_module.RestoreNotConfirmedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"id": str(request.id), "status": request.status.value}


sentry_webhook_router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@sentry_webhook_router.post("/webhooks/sentry", status_code=202)
async def receive_sentry_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    """Reçoit les alertes Sentry (règle d'alerte configurée côté Sentry, ex. "même erreur
    >= 5 fois en 1h" — le seuil lui-même vit dans Sentry, pas réimplémenté ici).

    Pas d'authentification ici : Sentry appelle cet endpoint directement et son propre
    mécanisme de vérification (signature HMAC du payload) n'est **pas implémenté** — à faire
    avant un vrai déploiement, sans quoi n'importe qui peut injecter de fausses alertes.
    Parsing best-effort : le schéma exact du payload Sentry n'a pas été vérifié contre la
    documentation à jour dans cette session (voir agents/maintenance/security_scan.py pour
    une note similaire sur pip-audit).
    """
    payload = await request.json()
    message = payload.get("data", {}).get("event", {}).get("message") or payload.get("message") or "Alerte Sentry (détail non extrait)"
    level = (payload.get("data", {}).get("event", {}).get("level") or "warning").lower()
    severity = NotificationSeverity.critical if level in {"error", "fatal"} else NotificationSeverity.warning

    notification = Notification(category=NotificationCategory.error_spike, severity=severity, message=str(message)[:1000])
    db.add(notification)
    db.commit()
    return {"received": True}
