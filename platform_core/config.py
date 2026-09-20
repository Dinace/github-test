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

    # Prospection — recherche de Pages professionnelles Meta (agents/prospection/sources/
    # meta_pages.py), deuxième source en plus de Google Places. Contrairement à
    # Client.meta_page_id/meta_page_access_token (le compte Meta DU CLIENT, utilisé par
    # l'agent Réseaux sociaux pour publier en son nom), ce sont des identifiants d'app Meta
    # au niveau PLATEFORME servant uniquement à interroger l'API Graph publique — jamais à
    # publier ni à agir au nom d'un client. Combinés en un jeton d'accès applicatif
    # (`{id}|{secret}`, format standard Meta). Vides par défaut : la recherche se limite
    # alors à Google Places, sans erreur (dégradation silencieuse).
    meta_app_id: str = ""
    meta_app_secret: str = ""

    # Chiffrement au repos des tokens sensibles stockés en base (Client.meta_page_access_token,
    # Client.whatsapp_access_token — voir platform_core/encryption.py). Clé Fernet
    # (`Fernet.generate_key()`), 44 caractères base64. Vide par défaut : dégradation
    # explicite en clair (pas de crash), pour ne pas casser le développement local/les tests
    # tant que la clé n'est pas configurée — mais à renseigner impérativement en production.
    token_encryption_key: str = ""

    # Secret partagé pour vérifier la signature HMAC des webhooks Sentry entrants
    # (app/routers/maintenance.py, en-tête `Sentry-Hook-Signature`). Vide par défaut : la
    # vérification est alors ignorée (comportement précédent, documenté comme non sécurisé)
    # plutôt que de rejeter tous les webhooks tant que le secret n'est pas configuré.
    sentry_webhook_secret: str = ""

    # Planning — rappels de RDV (agents/planning/scheduled_jobs.py). Compte WhatsApp
    # Business de la PLATEFORME (l'équipe qui opère la plateforme), distinct du compte
    # WhatsApp de chaque CLIENT (Client.whatsapp_phone_number_id/whatsapp_access_token,
    # utilisé par l'agent Prospection pour que le client contacte SES PROPRES prospects) :
    # ici c'est le staff qui contacte le client, jamais l'inverse. Vide par défaut : le job
    # ne fait rien tant que ces deux variables ne sont pas configurées (dégradation
    # silencieuse, cohérente avec les autres tâches planifiées sans credentials).
    platform_whatsapp_phone_number_id: str = ""
    platform_whatsapp_access_token: str = ""


settings = Settings()
