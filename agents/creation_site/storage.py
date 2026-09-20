"""Stockage des sites générés sur Cloudflare R2 (API compatible S3).

Deux préfixes dans le même bucket (agents/creation_site/skills/README.md) :
- `draft/<site_id>/...` : brouillon, jamais servi publiquement tant que non validé.
- `live/<site_id>/...`  : version publiée, promue depuis `draft/` à la validation client.

Le client S3 est injectable (`s3_client=...`) pour les tests, qui utilisent un faux client
plutôt que des credentials R2 réels (voir tests/test_creation_site_storage.py). Limite
connue : `promote_to_live` ne pagine pas au-delà des 1000 premiers objets retournés par
`list_objects_v2` — largement suffisant pour un site statique (quelques fichiers), à revoir
si un site venait à dépasser ce volume d'assets.
"""

import uuid
from typing import Any

import boto3

from platform_core.config import settings


def get_r2_client() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.cloudflare_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.cloudflare_r2_access_key_id,
        aws_secret_access_key=settings.cloudflare_r2_secret_access_key,
        region_name="auto",
    )


def upload_draft(site_id: uuid.UUID, html: str, *, s3_client: Any = None) -> str:
    """Écrit le site généré sous draft/<site_id>/index.html. Retourne la clé écrite."""
    s3_client = s3_client or get_r2_client()
    key = f"draft/{site_id}/index.html"
    s3_client.put_object(
        Bucket=settings.cloudflare_r2_bucket,
        Key=key,
        Body=html.encode("utf-8"),
        ContentType="text/html; charset=utf-8",
    )
    return key


def promote_to_live(site_id: uuid.UUID, *, s3_client: Any = None) -> list[str]:
    """Copie tous les objets sous draft/<site_id>/ vers live/<site_id>/.

    Appelé à la validation client (POST /api/sites/{id}/publish) — c'est ce qui rend le
    site effectivement public.
    """
    s3_client = s3_client or get_r2_client()
    bucket = settings.cloudflare_r2_bucket
    draft_prefix = f"draft/{site_id}/"
    live_prefix = f"live/{site_id}/"

    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=draft_prefix)
    promoted: list[str] = []
    for obj in response.get("Contents", []):
        draft_key = obj["Key"]
        live_key = live_prefix + draft_key.removeprefix(draft_prefix)
        s3_client.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": draft_key}, Key=live_key)
        promoted.append(live_key)

    return promoted
