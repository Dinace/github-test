"""Écriture du site généré dans l'espace de brouillon.

Implémentation actuelle : écriture sur disque local, simulant le préfixe `draft/` sur
Cloudflare R2 décrit dans agents/creation_site/skills/README.md (cycle brouillon ->
validation -> publication). Le remplacement par un upload réel vers R2 (API compatible S3)
nécessite des credentials R2 réels pour être testé — volontairement pas fait ici, voir TODO.
"""

import uuid
from pathlib import Path

_DRAFT_DIR = Path("output/draft")


def write_draft(site_id: uuid.UUID, html: str) -> Path:
    site_dir = _DRAFT_DIR / str(site_id)
    site_dir.mkdir(parents=True, exist_ok=True)
    index_path = site_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


# TODO(R2) : remplacer write_draft par un upload vers Cloudflare R2 (préfixe draft/<site_id>/)
# une fois CLOUDFLARE_R2_* renseignés dans config/credentials/.env (voir platform_core.config
# pour l'ajout des champs correspondants). Prévoir aussi promote_to_live(site_id) qui copie
# draft/<site_id>/ vers live/<site_id>/ au moment de la validation client.
