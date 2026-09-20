"""Tâche planifiée : rappel de rendez-vous par WhatsApp.

Décision actée dans cette session (jusqu'ici explicitement en attente, voir MEMORY.md) :
c'est le STAFF qui initie le rappel vers le client, jamais l'inverse — contrairement à
l'agent Prospection, où c'est le client qui contacte ses propres prospects via SON PROPRE
compte WhatsApp Business (`Client.whatsapp_phone_number_id`/`whatsapp_access_token`). Un
rappel de RDV a donc besoin de deux informations qui n'existaient pas encore :
- `Client.contact_phone` — le numéro à contacter (pas un compte WhatsApp Business, juste un
  numéro de contact de la PME) ;
- `settings.platform_whatsapp_phone_number_id`/`platform_whatsapp_access_token` — le compte
  WhatsApp Business de la PLATEFORME elle-même, pas celui d'un client, puisque c'est
  l'équipe qui parle en son nom propre.

Réutilise `agents.prospection.whatsapp.send_whatsapp_message` (même précédent que
Maintenance réutilisant `agents.creation_site.storage.get_r2_client` : un seul module par
intégration technique, pas une copie par agent) — l'agent Planning ne fait qu'appeler ce
module, il n'écrit jamais dans le périmètre de données de l'agent Prospection.
"""

from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from agents.prospection import whatsapp
from platform_core.config import settings
from platform_core.models import (
    Appointment,
    AppointmentStatus,
    Client,
    Notification,
    NotificationCategory,
    NotificationSeverity,
    NotificationStatus,
)

# Fenêtre de rappel : un rendez-vous dont l'échéance tombe dans les 24h reçoit un rappel.
# Choisi comme un compromis raisonnable (assez tôt pour permettre un report, assez tard pour
# rester pertinent) — pas encore configurable par pack ni par client, à revoir si le besoin
# d'un rappel à plusieurs échéances (ex. J-1 et H-1) se confirme.
_REMINDER_WINDOW = timedelta(hours=24)


def send_appointment_reminders(session_factory: Callable[[], AbstractContextManager[Session]]) -> None:
    if not settings.platform_whatsapp_phone_number_id or not settings.platform_whatsapp_access_token:
        return  # compte WhatsApp de la plateforme non configuré : rien à envoyer.

    with session_factory() as db:
        # Convention naïve-mais-UTC pour toute arithmétique contre une colonne DateTime de la
        # base (voir agents/maintenance/scheduled_jobs.py::_now_naive_utc pour la justification
        # empirique : ces colonnes perdent leur tzinfo, aware ou pas, sur SQLite comme sur
        # PostgreSQL).
        now = datetime.now(UTC).replace(tzinfo=None)
        window_end = now + _REMINDER_WINDOW

        due_appointments = (
            db.query(Appointment)
            .filter(
                Appointment.status.in_((AppointmentStatus.proposed, AppointmentStatus.confirmed)),
                Appointment.scheduled_at >= now,
                Appointment.scheduled_at <= window_end,
                Appointment.reminder_sent_at.is_(None),
            )
            .all()
        )

        for appointment in due_appointments:
            client = db.get(Client, appointment.client_id)
            if not client.contact_phone:
                continue  # aucun numéro de contact renseigné pour ce client : on ne peut pas le joindre.

            message = (
                f"Rappel : rendez-vous \"{appointment.purpose}\" prévu le "
                f"{appointment.scheduled_at.strftime('%d/%m/%Y à %H:%M')} avec notre équipe."
            )
            try:
                whatsapp.send_whatsapp_message(
                    settings.platform_whatsapp_phone_number_id,
                    settings.platform_whatsapp_access_token,
                    client.contact_phone,
                    message,
                )
            except whatsapp.WhatsAppSendError as exc:
                # Notifie le staff plutôt que de réessayer en silence indéfiniment — même
                # principe que agents/reseaux_sociaux/scheduled_jobs.py::publish_due_posts :
                # une seule notification par rendez-vous tant qu'elle n'est pas acquittée.
                already_notified = (
                    db.query(Notification)
                    .filter(
                        Notification.client_id == client.id,
                        Notification.category == NotificationCategory.error_spike,
                        Notification.status == NotificationStatus.pending,
                        Notification.message.contains(str(appointment.id)),
                    )
                    .first()
                )
                if already_notified is None:
                    db.add(
                        Notification(
                            category=NotificationCategory.error_spike,
                            severity=NotificationSeverity.warning,
                            message=(
                                f"Échec de l'envoi du rappel WhatsApp pour le rendez-vous {appointment.id} "
                                f"(client {client.name}) : {exc}"
                            ),
                            client_id=client.id,
                        )
                    )
                continue

            appointment.reminder_sent_at = now

        db.commit()
