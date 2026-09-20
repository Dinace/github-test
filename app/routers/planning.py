import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.planning import appointments as appointments_module
from agents.planning.dashboard import get_client_activity_summary
from agents.planning.digest import generate_digest
from agents.planning.pipeline import get_prospect_pipeline
from app.auth import get_current_client, require_ops_token
from platform_core.db import get_db
from platform_core.models import Appointment, Client

# Endpoints staff (équipe de la plateforme) : nécessitent OPS_API_TOKEN, même stopgap
# d'authentification que l'agent Maintenance (voir app/auth.py::require_ops_token).
staff_router = APIRouter(prefix="/api/planning", tags=["planning"], dependencies=[Depends(require_ops_token)])

# Endpoints propres au client authentifié par sa clé API (voir get_current_client).
client_router = APIRouter(prefix="/api/planning/me", tags=["planning"])


class ProposeAppointmentRequest(BaseModel):
    client_id: uuid.UUID
    staff_contact: str
    purpose: str
    scheduled_at: datetime
    duration_minutes: int = 30


class CompleteAppointmentRequest(BaseModel):
    notes: str | None = None


def _serialize_appointment(appointment: Appointment) -> dict:
    return {
        "id": str(appointment.id),
        "client_id": str(appointment.client_id),
        "staff_contact": appointment.staff_contact,
        "purpose": appointment.purpose,
        "scheduled_at": appointment.scheduled_at.isoformat(),
        "duration_minutes": appointment.duration_minutes,
        "status": appointment.status.value,
        "notes": appointment.notes,
    }


# --- Staff ---


@staff_router.get("/clients/{client_id}/summary")
def staff_get_client_summary(client_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return get_client_activity_summary(client_id, db=db).model_dump()


@staff_router.get("/clients/{client_id}/digest")
def staff_get_client_digest(client_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    summary = get_client_activity_summary(client_id, db=db)
    return {"summary": summary.model_dump(), "digest": generate_digest(summary)}


@staff_router.get("/prospects/{prospect_id}/pipeline")
def staff_get_prospect_pipeline(prospect_id: uuid.UUID, db: Session = Depends(get_db)) -> list[dict]:
    return [event.model_dump() for event in get_prospect_pipeline(prospect_id, db=db)]


@staff_router.post("/appointments", status_code=201)
def staff_propose_appointment(payload: ProposeAppointmentRequest, db: Session = Depends(get_db)) -> dict:
    appointment = appointments_module.propose_appointment(
        payload.client_id,
        payload.staff_contact,
        payload.purpose,
        payload.scheduled_at,
        payload.duration_minutes,
        db=db,
    )
    return _serialize_appointment(appointment)


@staff_router.get("/appointments")
def staff_list_appointments(db: Session = Depends(get_db)) -> list[dict]:
    appointments = db.query(Appointment).order_by(Appointment.scheduled_at).all()
    return [_serialize_appointment(a) for a in appointments]


@staff_router.post("/appointments/{appointment_id}/complete")
def staff_complete_appointment(
    appointment_id: uuid.UUID, payload: CompleteAppointmentRequest, db: Session = Depends(get_db)
) -> dict:
    try:
        appointment = appointments_module.complete_appointment(appointment_id, payload.notes, db=db)
    except appointments_module.AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize_appointment(appointment)


# --- Client ---


@client_router.get("/summary")
def get_my_summary(current_client: Client = Depends(get_current_client), db: Session = Depends(get_db)) -> dict:
    return get_client_activity_summary(current_client.id, db=db).model_dump()


@client_router.get("/appointments")
def list_my_appointments(current_client: Client = Depends(get_current_client), db: Session = Depends(get_db)) -> list[dict]:
    appointments = (
        db.query(Appointment)
        .filter(Appointment.client_id == current_client.id)
        .order_by(Appointment.scheduled_at)
        .all()
    )
    return [_serialize_appointment(a) for a in appointments]


def _get_owned_appointment(appointment_id: uuid.UUID, current_client: Client, db: Session) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    if appointment.client_id != current_client.id:
        raise HTTPException(status_code=403, detail="Ce rendez-vous n'appartient pas au client authentifié")
    return appointment


@client_router.post("/appointments/{appointment_id}/confirm")
def confirm_my_appointment(
    appointment_id: uuid.UUID, current_client: Client = Depends(get_current_client), db: Session = Depends(get_db)
) -> dict:
    _get_owned_appointment(appointment_id, current_client, db)
    appointment = appointments_module.confirm_appointment(appointment_id, db=db)
    return _serialize_appointment(appointment)


@client_router.post("/appointments/{appointment_id}/cancel")
def cancel_my_appointment(
    appointment_id: uuid.UUID, current_client: Client = Depends(get_current_client), db: Session = Depends(get_db)
) -> dict:
    _get_owned_appointment(appointment_id, current_client, db)
    appointment = appointments_module.cancel_appointment(appointment_id, db=db)
    return _serialize_appointment(appointment)
