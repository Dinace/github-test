"""Gestion des rendez-vous entre l'équipe de la plateforme (staff) et un client PME.

Décision actée avec l'utilisateur : RDV staff <-> client, pas un module de prise de RDV
grand public pour les clients finaux du PME (voir platform_core.models.Appointment).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from platform_core.models import Appointment, AppointmentStatus


class AppointmentNotFoundError(RuntimeError):
    pass


def propose_appointment(
    client_id: uuid.UUID,
    staff_contact: str,
    purpose: str,
    scheduled_at: datetime,
    duration_minutes: int,
    *,
    db: Session,
) -> Appointment:
    appointment = Appointment(
        client_id=client_id,
        staff_contact=staff_contact,
        purpose=purpose,
        scheduled_at=scheduled_at,
        duration_minutes=duration_minutes,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def _get_appointment(appointment_id: uuid.UUID, *, db: Session) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise AppointmentNotFoundError(f"Rendez-vous introuvable : {appointment_id}")
    return appointment


def confirm_appointment(appointment_id: uuid.UUID, *, db: Session) -> Appointment:
    appointment = _get_appointment(appointment_id, db=db)
    appointment.status = AppointmentStatus.confirmed
    appointment.confirmed_at = datetime.now(UTC)
    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(appointment_id: uuid.UUID, *, db: Session) -> Appointment:
    appointment = _get_appointment(appointment_id, db=db)
    appointment.status = AppointmentStatus.cancelled
    db.commit()
    db.refresh(appointment)
    return appointment


def complete_appointment(appointment_id: uuid.UUID, notes: str | None, *, db: Session) -> Appointment:
    appointment = _get_appointment(appointment_id, db=db)
    appointment.status = AppointmentStatus.completed
    appointment.notes = notes
    db.commit()
    db.refresh(appointment)
    return appointment
