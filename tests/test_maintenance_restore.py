from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.maintenance.restore import (
    RestoreNotConfirmedError,
    confirm_restore,
    execute_restore,
    propose_restore,
)
from platform_core.db import Base
from platform_core.models import Backup, RestoreStatus


@pytest.fixture()
def db_session(tmp_path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


@pytest.fixture()
def backup(db_session: Session) -> Backup:
    record = Backup(r2_key="backups/20260101T000000Z.sql", size_bytes=42)
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


def test_propose_restore_creates_pending_request(db_session: Session, backup: Backup) -> None:
    request = propose_restore(backup.id, "Site cassé après une mise à jour cliente", db=db_session)

    assert request.status == RestoreStatus.proposed
    assert request.confirmed_by is None


def test_execute_restore_refuses_without_confirmation(db_session: Session, backup: Backup) -> None:
    request = propose_restore(backup.id, "Test", db=db_session)

    with pytest.raises(RestoreNotConfirmedError):
        execute_restore(request.id, db=db_session)


def test_confirm_then_execute_restore_succeeds(db_session: Session, backup: Backup) -> None:
    class _FakeBody:
        def read(self) -> bytes:
            return b"-- dump --"

    class _FakeS3Client:
        def get_object(self, *, Bucket: str, Key: str) -> dict:
            return {"Body": _FakeBody()}

    executed_commands: list[list[str]] = []

    def fake_run_command(cmd: list[str], *, input: bytes, check: bool):  # noqa: A002
        executed_commands.append(cmd)

        class _Result:
            returncode = 0

        return _Result()

    request = propose_restore(backup.id, "Test", db=db_session)
    confirm_restore(request.id, "admin@example.com", db=db_session)

    result = execute_restore(
        request.id, db=db_session, run_command=fake_run_command, s3_client=_FakeS3Client()
    )

    assert result.status == RestoreStatus.executed
    assert result.executed_at is not None
    assert len(executed_commands) == 1
