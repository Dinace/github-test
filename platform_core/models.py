import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from platform_core.db import Base
from platform_core.encryption import decrypt_token, encrypt_token


def _utcnow() -> datetime:
    return datetime.now(UTC)


# JSONB sur PostgreSQL (choix acté, CLAUDE.md §3), JSON générique en repli sur les autres
# dialectes (ex. SQLite en test) où JSONB n'est pas compilable.
# none_as_null=True : par défaut, SQLAlchemy stocke un None Python comme un littéral JSON
# "null" (pas un vrai NULL SQL) — une colonne "vide" ne serait alors jamais NULL au sens
# SQL, cassant tout filtre `.is_(None)`/`.isnot(None)` (découvert via agents/planning/
# dashboard.py, qui filtre justement sur Site.content IS NOT NULL).
_JSONB = JSON(none_as_null=True).with_variant(JSONB(none_as_null=True), "postgresql")


class EncryptedString(TypeDecorator):
    """Colonne `String` chiffrée au repos (Fernet, voir platform_core/encryption.py).

    Chiffre/déchiffre de façon transparente pour le code applicatif (qui manipule toujours
    le texte en clair) ; c'est la valeur stockée en base qui est le ciphertext. Longueur
    doublée par rapport à la colonne en clair pour absorber le surcoût du chiffrement Fernet
    (base64 + IV + HMAC).
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt_token(value)

    def process_result_value(self, value, dialect):
        return decrypt_token(value)


class Pack(str, Enum):
    starter = "starter"
    business = "business"
    premium = "premium"


class Client(Base):
    """Un client de la plateforme (PME/indépendant)."""

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str] = mapped_column(String(100))
    # ISO 3166-1 alpha-2 ; "GA" = Gabon, pays de lancement (CLAUDE.md §1). Jamais codé en
    # dur ailleurs dans l'app : ce champ pilote devise et moyens de paiement disponibles.
    country: Mapped[str] = mapped_column(String(2), default="GA")
    currency: Mapped[str] = mapped_column(String(3), default="XAF")  # ISO 4217
    # Hash SHA-256 (hex, 64 caractères) de la clé API du client — jamais la clé en clair
    # (voir platform_core/auth.py pour la justification du choix SHA-256 plutôt que
    # bcrypt/argon2 dans ce cas précis).
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # Ton/voix de marque, défini une fois à l'onboarding (agents/reseaux_sociaux/skills/
    # README.md) et réutilisé pour chaque génération de contenu réseaux sociaux.
    brand_voice: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Connexion Meta (Facebook/Instagram) du client — renseignés manuellement pour l'instant,
    # le flux OAuth de connexion n'est pas implémenté (agents/reseaux_sociaux/skills/
    # README.md, "points à trancher"). Stockage en clair : à chiffrer au repos si ce champ
    # devient sensible en pratique (c'est un token appartenant au client, pas un secret
    # plateforme, mais un durcissement reste souhaitable avant une vraie mise en prod).
    meta_page_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Chiffré au repos (EncryptedString, voir plus haut) : ce sont des tokens d'accès
    # permettant de publier au nom du client, pas de simples identifiants. Longueur 1000
    # (vs 500 en clair) pour absorber le surcoût du ciphertext Fernet.
    meta_page_access_token: Mapped[str | None] = mapped_column(EncryptedString(1000), nullable=True)
    # Connexion WhatsApp Business Cloud API du client (agent Prospection, premier contact).
    # Renseignés manuellement, pas de flux de connexion automatisé (voir
    # agents/prospection/skills/README.md).
    whatsapp_phone_number_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    whatsapp_access_token: Mapped[str | None] = mapped_column(EncryptedString(1000), nullable=True)
    # Numéro de contact de la PME côté staff (agent Planning : rappels de RDV) — distinct de
    # whatsapp_phone_number_id ci-dessus, qui est le compte WhatsApp Business DU CLIENT pour
    # contacter SES PROPRES prospects (agent Prospection). Ici c'est l'inverse : le STAFF
    # de la plateforme contacte CE numéro, via le compte WhatsApp Business de la PLATEFORME
    # (settings.platform_whatsapp_*), pas celui du client. Pas de flux de saisie dédié pour
    # l'instant : renseigné manuellement en base, comme les autres champs de contact.
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Note libre côté staff (agent Planning, "office manager") — infos utiles au projet non
    # capturées ailleurs (ex. contrainte particulière évoquée au téléphone, préférence de
    # contact...). Jamais montré au client, jamais structuré : un vrai besoin récurrent
    # identifié ici mériterait un champ dédié plutôt que de rester dans ce texte libre.
    project_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    subscription: Mapped["Subscription | None"] = relationship(back_populates="client", uselist=False)


class Subscription(Base):
    """Abonnement actif d'un client à un pack (CLAUDE.md §1)."""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    pack: Mapped[Pack] = mapped_column(SAEnum(Pack, name="pack_enum"))
    # Montant dans la plus petite unité de la devise (le FCFA n'a pas de sous-unité, donc
    # c'est directement le montant en FCFA pour price_currency="XAF").
    price_amount: Mapped[int] = mapped_column()
    price_currency: Mapped[str] = mapped_column(String(3), default="XAF")
    # Nom du provider actif pour ce client (ex. "orange_money", "airtel_money",
    # "moov_money") — paramétrable par pays/client, jamais une liste figée (CLAUDE.md §1).
    payment_provider: Mapped[str] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    client: Mapped["Client"] = relationship(back_populates="subscription")


class SiteStatus(str, Enum):
    draft = "draft"
    published = "published"


class Site(Base):
    """Site généré pour un client par l'agent Création de site.

    Cycle brouillon → validation → publication (agents/creation_site/skills/README.md) :
    un site reste `draft` tant que le client ne l'a pas validé ; seule cette validation fait
    passer `status` à `published` et fixe `published_at`.
    """

    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    # Clé du secteur, doit correspondre à un template de agents/creation_site/templates/
    # (catalogue défini dans agents/creation_site/skills/README.md).
    sector: Mapped[str] = mapped_column(String(50))
    brief: Mapped[dict] = mapped_column(_JSONB)
    content: Mapped[dict | None] = mapped_column(_JSONB, nullable=True)
    status: Mapped[SiteStatus] = mapped_column(SAEnum(SiteStatus, name="site_status_enum"), default=SiteStatus.draft)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Surveillance de disponibilité (agents/maintenance/uptime.py) — renseigné manuellement
    # pour l'instant (pas de création automatique de monitor UptimeRobot à la publication du
    # site). Tant qu'il est vide, la tâche planifiée de vérification d'uptime ignore ce site.
    uptime_monitor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_uptime_check_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Horodatage du début de l'indisponibilité en cours (remis à None dès que le site est de
    # nouveau up) — nécessaire pour appliquer le seuil des 15 minutes de
    # uptime.should_notify_downtime avant de notifier un humain.
    down_since: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    client: Mapped["Client"] = relationship()


class NotificationCategory(str, Enum):
    site_down = "site_down"
    backup_failure = "backup_failure"
    security_finding = "security_finding"
    error_spike = "error_spike"


class NotificationSeverity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class NotificationStatus(str, Enum):
    pending = "pending"
    acknowledged = "acknowledged"


class Notification(Base):
    """Anomalie détectée par l'agent Maintenance nécessitant l'attention d'un humain
    (agents/maintenance/skills/README.md, "seuils de notification humaine").

    Rattachée à un client/site quand pertinent (ex. site indisponible), mais gérée par le
    staff, pas par le client lui-même — pas d'authentification par clé API client ici,
    voir app/routers/maintenance.py.
    """

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[NotificationCategory] = mapped_column(SAEnum(NotificationCategory, name="notif_category_enum"))
    severity: Mapped[NotificationSeverity] = mapped_column(SAEnum(NotificationSeverity, name="notif_severity_enum"))
    message: Mapped[str] = mapped_column(String(1000))
    client_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clients.id"), nullable=True)
    site_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sites.id"), nullable=True)
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(NotificationStatus, name="notif_status_enum"), default=NotificationStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Backup(Base):
    """Sauvegarde de la base de données (agents/maintenance/backup.py).

    Platform-wide, pas par client : PostgreSQL est une base partagée entre tous les clients
    (CLAUDE.md §3), donc un pg_dump couvre toute la plateforme, pas un client isolé.
    """

    __tablename__ = "backups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    r2_key: Mapped[str] = mapped_column(String(255), unique=True)
    size_bytes: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class RestoreStatus(str, Enum):
    proposed = "proposed"
    confirmed = "confirmed"
    executed = "executed"
    rejected = "rejected"


class RestoreRequest(Base):
    """Demande de restauration : propose -> confirmation humaine -> exécution.

    Jamais exécutée automatiquement (CLAUDE.md §5, agents/maintenance/skills/README.md,
    "processus de restauration") — agents/maintenance/restore.py refuse execute_restore tant
    que status != confirmed.
    """

    __tablename__ = "restore_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    backup_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("backups.id"))
    reason: Mapped[str] = mapped_column(String(1000))
    status: Mapped[RestoreStatus] = mapped_column(SAEnum(RestoreStatus, name="restore_status_enum"), default=RestoreStatus.proposed)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    confirmed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PostStatus(str, Enum):
    draft = "draft"
    pending_validation = "pending_validation"
    validated = "validated"
    scheduled = "scheduled"
    published = "published"


class Post(Base):
    """Publication réseaux sociaux pour un client, gérée par l'agent Réseaux sociaux.

    Workflow à statuts strict (agents/reseaux_sociaux/skills/README.md), aucun raccourci :
    draft -> pending_validation -> validated -> scheduled -> published. Seule la transition
    validated -> published (via /publish) déclenche l'appel réel à l'API Meta.
    """

    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    brief: Mapped[dict] = mapped_column(_JSONB)
    content: Mapped[dict | None] = mapped_column(_JSONB, nullable=True)
    status: Mapped[PostStatus] = mapped_column(SAEnum(PostStatus, name="post_status_enum"), default=PostStatus.draft)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    client: Mapped["Client"] = relationship()


class ProspectCategory(str, Enum):
    """4 catégories actées (CLAUDE.md §5, agents/prospection/skills/README.md)."""

    favorable = "favorable"
    a_qualifier = "a_qualifier"
    non_favorable = "non_favorable"
    non_joignable = "non_joignable"


class ContactStatus(str, Enum):
    none = "none"
    draft = "draft"
    pending_validation = "pending_validation"
    validated = "validated"
    sent = "sent"


class Prospect(Base):
    """Fiche prospect trouvée pour le compte d'un client (agent Prospection commerciale).

    Le scoring (category/score) est calculé par agents/prospection/scoring.py au moment de
    la création — jamais recalculé "à la volée" pour éviter qu'un prospect déjà classé
    "non favorable"/"non joignable" ne redevienne contactable sans repasser par une nouvelle
    collecte explicite.
    """

    __tablename__ = "prospects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    business_name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # "google_places" | "meta_page" | "directory" — jamais "linkedin" (voir agents/
    # prospection/compliance.py, vérifié en code, pas seulement documenté).
    source: Mapped[str] = mapped_column(String(50))
    raw_data: Mapped[dict] = mapped_column(_JSONB)
    category: Mapped[ProspectCategory] = mapped_column(SAEnum(ProspectCategory, name="prospect_category_enum"))
    score: Mapped[int] = mapped_column()
    contact_message: Mapped[dict | None] = mapped_column(_JSONB, nullable=True)
    contact_status: Mapped[ContactStatus] = mapped_column(
        SAEnum(ContactStatus, name="contact_status_enum"), default=ContactStatus.none
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    contacted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    client: Mapped["Client"] = relationship()


class ActivityEvent(Base):
    """Journal d'événements partagé entre agents (agents/planning/skills/README.md).

    Contrairement aux autres tables (chacune "possédée" par un agent), celle-ci vit dans
    `platform_core` — le package partagé — précisément parce qu'elle est écrite par
    plusieurs agents (ex. Prospection) et lue par l'agent Planning pour reconstituer un
    historique. Ce n'est pas une exception au cloisonnement (CLAUDE.md §5, "ne jamais
    modifier les données d'un autre agent") : chaque agent n'écrit que SES PROPRES
    événements ici, jamais les données propres d'un autre agent (Site, Post, Prospect...).
    """

    __tablename__ = "activity_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    # "creation_site" | "reseaux_sociaux" | "maintenance" | "prospection" — l'agent qui a
    # émis l'événement, jamais un autre.
    agent: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(_JSONB, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class AppointmentStatus(str, Enum):
    proposed = "proposed"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class Appointment(Base):
    """Rendez-vous entre l'équipe de la plateforme (staff) et un client PME.

    Décision actée avec l'utilisateur : ces RDV sont staff <-> client (onboarding, suivi
    commercial, support), pas des RDV grand public pour les clients FINAUX du PME — ce
    dernier usage (ex. réservation restaurant) resterait un besoin distinct, non couvert ici.
    """

    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    # Nom/email de la personne côté staff — pas de compte staff individuel pour l'instant
    # (même limite que OPS_API_TOKEN pour l'agent Maintenance).
    staff_contact: Mapped[str] = mapped_column(String(255))
    purpose: Mapped[str] = mapped_column(String(255))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(default=30)
    status: Mapped[AppointmentStatus] = mapped_column(
        SAEnum(AppointmentStatus, name="appointment_status_enum"), default=AppointmentStatus.proposed
    )
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    # Horodatage du dernier rappel WhatsApp envoyé (agents/planning/scheduled_jobs.py) — évite
    # de renvoyer un rappel à chaque tick tant que le rendez-vous reste proposed/confirmed.
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    client: Mapped["Client"] = relationship()


class OnboardingTeam(str, Enum):
    commercial = "commercial"
    technique = "technique"


class OnboardingNotificationStatus(str, Enum):
    pending = "pending"
    acknowledged = "acknowledged"


class OnboardingNotification(Base):
    """Notification précise envoyée à une équipe interne lors de la progression d'une étape
    de mise en place de l'offre chez un client — extension "office manager" de l'agent
    Planning (décision actée avec l'utilisateur : pas un agent séparé, voir MEMORY.md et
    agents/planning/skills/README.md).

    Modèle **distinct** de `Notification` ci-dessus (qui reste la notification d'anomalie
    technique de l'agent Maintenance, périmètre et audience différents — l'équipe commerciale
    n'a pas à voir "scan de sécurité : aucune vulnérabilité" et l'équipe Maintenance n'a pas
    à voir "site publié"). Les créer dans la même table aurait aussi violé le cloisonnement
    (CLAUDE.md §5) : `Notification` est possédée par l'agent Maintenance.
    """

    __tablename__ = "onboarding_notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    # Clé technique de l'étape franchie (ex. "site_published") — voir
    # agents/planning/onboarding.py pour la liste des étapes.
    step_key: Mapped[str] = mapped_column(String(100))
    team: Mapped[OnboardingTeam] = mapped_column(SAEnum(OnboardingTeam, name="onboarding_team_enum"))
    message: Mapped[str] = mapped_column(String(500))
    status: Mapped[OnboardingNotificationStatus] = mapped_column(
        SAEnum(OnboardingNotificationStatus, name="onboarding_notif_status_enum"),
        default=OnboardingNotificationStatus.pending,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    client: Mapped["Client"] = relationship()
