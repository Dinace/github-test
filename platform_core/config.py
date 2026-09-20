from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="config/credentials/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://localhost/digitalisation_dev"
    environment: str = "development"

    # Cloudflare R2 (voir config/credentials/README.md) — vides par défaut : seul le code
    # qui appelle réellement R2 (agents/creation_site/storage.py) en a besoin ; les tests
    # injectent un client S3 simulé et n'ont pas besoin de ces valeurs.
    cloudflare_account_id: str = ""
    cloudflare_r2_access_key_id: str = ""
    cloudflare_r2_secret_access_key: str = ""
    cloudflare_r2_bucket: str = ""

    # Maintenance (voir config/credentials/README.md).
    sentry_dsn: str = ""
    uptime_monitor_token: str = ""
    # Jeton partagé pour les endpoints internes de Maintenance (app/routers/maintenance.py).
    # STOPGAP explicite : ce n'est pas un vrai système d'auth staff (comptes individuels,
    # rôles, audit par utilisateur) — un verrou minimal en attendant que ce système soit
    # conçu. Vide par défaut : les endpoints concernés répondent alors 503 plutôt que de
    # s'ouvrir en clair si la variable n'est pas configurée.
    ops_api_token: str = ""

    # Prospection — clé simple pour Google Places API (distincte de
    # GOOGLE_BUSINESS_PROFILE_TOKEN, qui gère la fiche établissement du client lui-même, pas
    # la recherche d'AUTRES établissements pour la prospection).
    google_places_api_key: str = ""


settings = Settings()
