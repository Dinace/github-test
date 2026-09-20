import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.planning.dashboard import get_client_activity_summary
from platform_core.auth import create_client_with_api_key
from platform_core.db import Base
from platform_core.models import ContactStatus, Post, PostStatus, Prospect, ProspectCategory, Site, SiteStatus


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


def test_summary_counts_items_needing_attention(db_session: Session, client_id: uuid.UUID) -> None:
    db_session.add(
        Site(client_id=client_id, sector="restaurant", brief={}, content={"hero_tagline": "x"}, status=SiteStatus.draft)
    )
    db_session.add(Site(client_id=client_id, sector="restaurant", brief={}, content=None, status=SiteStatus.draft))
    db_session.add(Post(client_id=client_id, brief={}, status=PostStatus.pending_validation))
    db_session.add(Post(client_id=client_id, brief={}, status=PostStatus.draft))
    db_session.add(
        Prospect(
            client_id=client_id,
            business_name="A",
            sector="boutique",
            source="google_places",
            raw_data={},
            category=ProspectCategory.a_qualifier,
            score=0,
        )
    )
    db_session.add(
        Prospect(
            client_id=client_id,
            business_name="B",
            sector="boutique",
            source="google_places",
            raw_data={},
            category=ProspectCategory.favorable,
            score=5,
            contact_status=ContactStatus.pending_validation,
        )
    )
    db_session.commit()

    summary = get_client_activity_summary(client_id, db=db_session)

    # Un seul des deux sites a du contenu généré ET est en draft -> compté.
    assert summary.sites_awaiting_validation == 1
    assert summary.posts_awaiting_validation == 1
    assert summary.prospects_to_qualify == 1
    assert summary.prospects_awaiting_contact_validation == 1


def test_summary_is_zero_for_client_with_no_activity(db_session: Session, client_id: uuid.UUID) -> None:
    summary = get_client_activity_summary(client_id, db=db_session)

    assert summary.sites_awaiting_validation == 0
    assert summary.posts_awaiting_validation == 0
    assert summary.prospects_to_qualify == 0
    assert summary.prospects_awaiting_contact_validation == 0
