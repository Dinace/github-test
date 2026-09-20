import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.planning.onboarding import get_onboarding_checklist
from platform_core.auth import create_client_with_api_key
from platform_core.db import Base
from platform_core.models import (
    Backup,
    Pack,
    Post,
    PostStatus,
    Prospect,
    ProspectCategory,
    Site,
    SiteStatus,
    Subscription,
)


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


def _subscribe(db: Session, client_id: uuid.UUID, pack: Pack) -> None:
    db.add(Subscription(client_id=client_id, pack=pack, price_amount=1000, payment_provider="orange_money"))
    db.commit()


def test_starter_checklist_has_no_social_or_prospection_steps(db_session: Session, client_id: uuid.UUID) -> None:
    _subscribe(db_session, client_id, Pack.starter)

    steps = get_onboarding_checklist(client_id, db=db_session)
    keys = {step.key for step in steps}

    assert "social_media_active" not in keys
    assert "prospection_started" not in keys
    assert keys == {"site_created", "site_content_generated", "site_published", "first_backup_confirmed"}
    assert all(step.done is False for step in steps)


def test_starter_checklist_reflects_site_progress(db_session: Session, client_id: uuid.UUID) -> None:
    _subscribe(db_session, client_id, Pack.starter)
    db_session.add(
        Site(
            client_id=client_id,
            sector="restaurant",
            brief={},
            content={"hero_tagline": "Bienvenue"},
            status=SiteStatus.published,
        )
    )
    db_session.commit()

    steps = {step.key: step.done for step in get_onboarding_checklist(client_id, db=db_session)}

    assert steps["site_created"] is True
    assert steps["site_content_generated"] is True
    assert steps["site_published"] is True


def test_business_pack_checklist_includes_social_and_prospection_steps(
    db_session: Session, client_id: uuid.UUID
) -> None:
    _subscribe(db_session, client_id, Pack.business)

    steps = {step.key: step for step in get_onboarding_checklist(client_id, db=db_session)}

    assert "social_media_active" in steps
    assert steps["social_media_active"].team == "commercial"
    assert steps["social_media_active"].done is False
    assert "prospection_started" in steps
    assert steps["prospection_started"].done is False


def test_business_pack_checklist_marks_social_and_prospection_done(db_session: Session, client_id: uuid.UUID) -> None:
    _subscribe(db_session, client_id, Pack.business)
    db_session.add(Post(client_id=client_id, brief={}, status=PostStatus.published))
    db_session.add(
        Prospect(
            client_id=client_id,
            business_name="Boutique X",
            sector="boutique",
            source="google_places",
            raw_data={},
            category=ProspectCategory.favorable,
            score=3,
        )
    )
    db_session.commit()

    steps = {step.key: step.done for step in get_onboarding_checklist(client_id, db=db_session)}

    assert steps["social_media_active"] is True
    assert steps["prospection_started"] is True


def test_backup_step_is_platform_wide(db_session: Session, client_id: uuid.UUID) -> None:
    """La sauvegarde est une ressource plateforme, pas par client (voir
    platform_core.models.Backup) : dès qu'une sauvegarde existe, l'étape est franchie pour
    n'importe quel client, y compris un client créé après coup."""
    _subscribe(db_session, client_id, Pack.starter)
    db_session.add(Backup(r2_key="backups/x.sql", size_bytes=10))
    db_session.commit()

    steps = {step.key: step.done for step in get_onboarding_checklist(client_id, db=db_session)}

    assert steps["first_backup_confirmed"] is True


def test_checklist_defaults_to_starter_without_active_subscription(db_session: Session, client_id: uuid.UUID) -> None:
    steps = {step.key for step in get_onboarding_checklist(client_id, db=db_session)}

    assert "social_media_active" not in steps
    assert "prospection_started" not in steps
