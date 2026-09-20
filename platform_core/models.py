import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from platform_core.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


# JSONB sur PostgreSQL (choix acté, CLAUDE.md §3), JSON générique en repli sur les autres
# dialectes (ex. SQLite en test) où JSONB n'est pas compilable.
_JSONB = JSON().with_variant(JSONB(), "postgresql")


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
    meta_page_access_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
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

    client: Mapped["Client"] = relationship()


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
