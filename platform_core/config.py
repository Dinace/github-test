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


settings = Settings()
