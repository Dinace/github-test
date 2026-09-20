import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.planning.appointments import (
    AppointmentNotFoundError,
    cancel_appointment,
    complete_appointment,
    confirm_appointment,
    propose_appointment,
)
from platform_core.auth import create_client_with_api_key
from platform_core.db import Base
from platform_core.models import AppointmentStatus


@pytest.fixture()
def db_session(tmp_path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


@pytest.fixture()
def client_id(db_session: Session) -> uuid.UUID:
    client, _api_key = create_client_with_api_key(db_session, name="Chez Awa", sector="restaurant")
    return client.id


def test_propose_then_confirm_appointment(db_session: Session, client_id: uuid.UUID) -> None:
    scheduled_at = datetime.now(UTC) + timedelta(days=2)

    appointment = propose_appointment(
        client_id, "success@plateforme.example", "Onboarding", scheduled_at, 45, db=db_session
    )
    assert appointment.status == AppointmentStatus.proposed

    confirmed = confirm_appointment(appointment.id, db=db_session)
    assert confirmed.status == AppointmentStatus.confirmed
    assert confirmed.confirmed_at is not None


def test_cancel_appointment(db_session: Session, client_id: uuid.UUID) -> None:
    scheduled_at = datetime.now(UTC) + timedelta(days=2)
    appointment = propose_appointment(client_id, "staff@example.com", "Support", scheduled_at, 30, db=db_session)

    cancelled = cancel_appointment(appointment.id, db=db_session)

    assert cancelled.status == AppointmentStatus.cancelled


def test_complete_appointment_stores_notes(db_session: Session, client_id: uuid.UUID) -> None:
    scheduled_at = datetime.now(UTC) + timedelta(days=2)
    appointment = propose_appointment(client_id, "staff@example.com", "Suivi commercial", scheduled_at, 30, db=db_session)

    completed = complete_appointment(appointment.id, "Client satisfait, souhaite passer au pack Business", db=db_session)

    assert completed.status == AppointmentStatus.completed
    assert "Business" in completed.notes


def test_confirm_appointment_not_found_raises(db_session: Session) -> None:
    with pytest.raises(AppointmentNotFoundError):
        confirm_appointment(uuid.uuid4(), db=db_session)
