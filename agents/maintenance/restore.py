"""Workflow de restauration : proposition -> confirmation humaine -> exécution.

Jamais d'exécution automatique (CLAUDE.md §5 ; agents/maintenance/skills/README.md,
"processus de restauration après incident") : execute_restore refuse tant que la demande
n'est pas au statut `confirmed`, quelle que soit la façon dont elle est appelée.
"""

import subprocess
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from platform_core.models import Backup, RestoreRequest, RestoreStatus


class RestoreRequestNotFoundError(RuntimeError):
    pass


class RestoreNotConfirmedError(RuntimeError):
    """Levée si on tente d'exécuter une restauration qui n'a pas été confirmée par un
    humain — c'est la garde-fou central de ce module, jamais à contourner."""


def propose_restore(backup_id: uuid.UUID, reason: str, *, db: Session) -> RestoreRequest:
    """L'agent propose une restauration ; ne l'exécute jamais lui-même."""
    request = RestoreRequest(backup_id=backup_id, reason=reason, status=RestoreStatus.proposed)
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def confirm_restore(restore_request_id: uuid.UUID, confirmed_by: str, *, db: Session) -> RestoreRequest:
    """Un humain confirme explicitement — action journalisée (qui, quand)."""
    request = db.get(RestoreRequest, restore_request_id)
    if request is None:
        raise RestoreRequestNotFoundError(f"Demande de restauration introuvable : {restore_request_id}")

    request.status = RestoreStatus.confirmed
    request.confirmed_by = confirmed_by
    request.confirmed_at = datetime.now(UTC)
    db.commit()
    db.refresh(request)
    return request


def execute_restore(
    restore_request_id: uuid.UUID,
    *,
    db: Session,
    run_command: Callable[..., subprocess.CompletedProcess] | None = None,
    s3_client: Any = None,
) -> RestoreRequest:
    request = db.get(RestoreRequest, restore_request_id)
    if request is None:
        raise RestoreRequestNotFoundError(f"Demande de restauration introuvable : {restore_request_id}")
    if request.status != RestoreStatus.confirmed:
        raise RestoreNotConfirmedError(
            f"Restauration refusée : statut actuel '{request.status.value}', 'confirmed' requis"
        )

    from agents.creation_site.storage import get_r2_client
    from platform_core.config import settings

    run_command = run_command or subprocess.run
    s3_client = s3_client or get_r2_client()

    backup = db.get(Backup, request.backup_id)
    obj = s3_client.get_object(Bucket=settings.cloudflare_r2_bucket, Key=backup.r2_key)
    dump_bytes = obj["Body"].read()

    run_command(["psql", settings.database_url], input=dump_bytes, check=True)

    request.status = RestoreStatus.executed
    request.executed_at = datetime.now(UTC)
    db.commit()
    db.refresh(request)
    return request
