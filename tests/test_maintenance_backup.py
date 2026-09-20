from datetime import UTC, datetime, timedelta

from platform_core.models import Pack


class _FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted: list[str] = []

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:
        self.objects[Key] = Body

    def list_objects_v2(self, *, Bucket: str, Prefix: str) -> dict:
        return {"Contents": [{"Key": k} for k in self.objects if k.startswith(Prefix)]}

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        self.deleted.append(Key)
        del self.objects[Key]


def _key(dt: datetime) -> str:
    return f"backups/{dt.strftime('%Y%m%dT%H%M%SZ')}.sql"


def test_upload_and_list_backup() -> None:
    from agents.maintenance.backup import list_backup_keys, upload_backup

    fake_client = _FakeS3Client()
    now = datetime.now(UTC)

    key = upload_backup(b"-- dump --", now, s3_client=fake_client)

    assert key == _key(now)
    assert list_backup_keys(s3_client=fake_client) == [key]


def test_starter_retention_keeps_one_backup_per_month_within_3_months() -> None:
    from agents.maintenance.backup import keys_to_retain

    now = datetime(2026, 9, 20, tzinfo=UTC)
    keys = [
        _key(now - timedelta(days=5)),  # septembre, récent
        _key(now - timedelta(days=10)),  # septembre, plus ancien -> pas retenu (doublon de mois)
        _key(now - timedelta(days=40)),  # août
        _key(now - timedelta(days=70)),  # juillet
        _key(now - timedelta(days=200)),  # bien trop vieux -> exclu
    ]

    retained = keys_to_retain(Pack.starter, keys, now=now)

    assert keys[0] in retained  # le plus récent de septembre
    assert keys[1] not in retained  # doublon du même mois, pas le plus récent
    assert keys[2] in retained
    assert keys[3] in retained
    assert keys[4] not in retained
    assert len(retained) == 3


def test_business_retention_keeps_weekly_then_monthly() -> None:
    from agents.maintenance.backup import keys_to_retain

    now = datetime(2026, 9, 20, tzinfo=UTC)
    keys = [
        _key(now - timedelta(days=3)),  # dans la fenêtre hebdo (<=56j)
        _key(now - timedelta(days=10)),  # dans la fenêtre hebdo, même semaine ISO probable
        _key(now - timedelta(days=100)),  # au-delà des 56j, dans la fenêtre mensuelle dérivée
        _key(now - timedelta(days=200)),  # trop vieux, exclu
    ]

    retained = keys_to_retain(Pack.business, keys, now=now)

    assert keys[2] in retained
    assert keys[3] not in retained
    # Les deux premiers sont dans la fenêtre hebdo : au moins le plus récent est conservé.
    assert keys[0] in retained


def test_premium_retention_keeps_all_recent_daily_backups() -> None:
    from agents.maintenance.backup import keys_to_retain

    now = datetime(2026, 9, 20, tzinfo=UTC)
    keys = [_key(now - timedelta(days=d)) for d in range(0, 30)]

    retained = keys_to_retain(Pack.premium, keys, now=now)

    # Fenêtre quotidienne : les 30 derniers jours sont TOUS conservés (pas de dérivation).
    assert retained == set(keys)


def test_apply_retention_deletes_keys_outside_window() -> None:
    from agents.maintenance.backup import apply_retention

    now = datetime(2026, 9, 20, tzinfo=UTC)
    fake_client = _FakeS3Client()
    old_key = _key(now - timedelta(days=400))
    recent_key = _key(now - timedelta(days=1))
    fake_client.objects[old_key] = b"old"
    fake_client.objects[recent_key] = b"recent"

    deleted = apply_retention(Pack.starter, s3_client=fake_client, now=now)

    assert old_key in deleted
    assert recent_key not in deleted
    assert recent_key in fake_client.objects
    assert old_key not in fake_client.objects
