import uuid

from agents.creation_site.storage import promote_to_live, upload_draft


class _FakeS3Client:
    """Simule le sous-ensemble de l'API S3 utilisé par storage.py, en mémoire."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:
        self.objects[Key] = Body

    def list_objects_v2(self, *, Bucket: str, Prefix: str) -> dict:
        matching = [{"Key": key} for key in self.objects if key.startswith(Prefix)]
        return {"Contents": matching}

    def copy_object(self, *, Bucket: str, CopySource: dict, Key: str) -> None:
        self.objects[Key] = self.objects[CopySource["Key"]]


def test_upload_draft_writes_expected_key() -> None:
    site_id = uuid.uuid4()
    fake_client = _FakeS3Client()

    key = upload_draft(site_id, "<html>Bonjour</html>", s3_client=fake_client)

    assert key == f"draft/{site_id}/index.html"
    assert fake_client.objects[key] == b"<html>Bonjour</html>"


def test_promote_to_live_copies_draft_objects_to_live_prefix() -> None:
    site_id = uuid.uuid4()
    fake_client = _FakeS3Client()
    upload_draft(site_id, "<html>Bonjour</html>", s3_client=fake_client)

    promoted = promote_to_live(site_id, s3_client=fake_client)

    expected_live_key = f"live/{site_id}/index.html"
    assert promoted == [expected_live_key]
    assert fake_client.objects[expected_live_key] == b"<html>Bonjour</html>"
    # Le brouillon original reste présent (on ne déplace pas, on copie).
    assert f"draft/{site_id}/index.html" in fake_client.objects


def test_promote_to_live_is_noop_when_nothing_drafted() -> None:
    site_id = uuid.uuid4()
    fake_client = _FakeS3Client()

    promoted = promote_to_live(site_id, s3_client=fake_client)

    assert promoted == []
