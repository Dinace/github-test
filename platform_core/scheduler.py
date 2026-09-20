"""Infrastructure de tâches planifiées (APScheduler), partagée par les agents Réseaux
sociaux, Maintenance et Planning — remplace les déclenchements manuels via API documentés
comme "point ouvert" dans leurs `skills/README.md` respectifs (pas de vraie tâche planifiée
avant l'ajout de ce module).

`BackgroundScheduler` (pas `AsyncIOScheduler`) : la logique métier existante est
synchrone (SQLAlchemy `Session`, clients HTTP synchrones) — `BackgroundScheduler` l'exécute
dans un thread du pool sans avoir à la réécrire en async pour ce seul besoin.

Chaque job ouvre sa propre `Session` SQLAlchemy à chaque exécution (comme le ferait une
tâche Celery), jamais une session partagée entre déclenchements : les jobs s'exécutent à des
instants différents, il ne faut pas garder de transaction ouverte entre deux exécutions.

Démarré depuis `app/main.py` (lifespan FastAPI) — jamais démarré par les tests, qui
instancient `TestClient(app)` sans bloc `with` (les événements de lifespan ne se déclenchent
alors pas), donc aucun job planifié ne tourne en arrière-plan pendant la suite de tests.
"""

import logging
from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler

from platform_core.db import SessionLocal

logger = logging.getLogger(__name__)


def _safe(name: str, job: Callable[[], None]) -> Callable[[], None]:
    """Isole chaque exécution de job : une exception ne doit jamais arrêter le scheduler
    (sinon plus aucun job suivant ne s'exécute), seulement être loggée."""

    def _wrapped() -> None:
        try:
            job()
        except Exception:
            logger.exception("Échec de la tâche planifiée '%s'", name)

    return _wrapped


def create_scheduler() -> BackgroundScheduler:
    # Imports différés : évite tout import circulaire (les modules de jobs importent
    # platform_core.models/db, pas ce module) et ne charge les agents qu'au démarrage réel
    # de l'app, pas à l'import de platform_core.scheduler.
    from agents.maintenance.scheduled_jobs import (
        run_backups_and_retention,
        run_security_scans,
        run_uptime_checks,
    )
    from agents.planning.scheduled_jobs import (
        notify_onboarding_progress,
        send_appointment_reminders,
    )
    from agents.reseaux_sociaux.scheduled_jobs import publish_due_posts

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _safe("publish_due_posts", lambda: publish_due_posts(SessionLocal)),
        "interval",
        minutes=5,
        id="publish_due_posts",
    )
    # Le tick ci-dessous est un plafond commun (le palier le plus fréquent, Premium —
    # "temps réel" approximé à 1 minute) : chaque site n'est effectivement re-vérifié qu'au
    # rythme de son propre pack, calculé dans le job lui-même (voir
    # agents/maintenance/scheduled_jobs.py::_UPTIME_INTERVALS).
    scheduler.add_job(
        _safe("run_uptime_checks", lambda: run_uptime_checks(SessionLocal)),
        "interval",
        minutes=1,
        id="run_uptime_checks",
    )
    # Idem : le job compare lui-même la dernière exécution réelle (Backup.created_at /
    # Notification.created_at) à l'intervalle dû pour l'abonnement actif le plus exigeant —
    # ce tick horaire ne fait que garantir une détection rapide de l'échéance, sans dupliquer
    # le travail si elle n'est pas encore atteinte.
    scheduler.add_job(
        _safe("run_backups_and_retention", lambda: run_backups_and_retention(SessionLocal)),
        "interval",
        hours=1,
        id="run_backups_and_retention",
    )
    scheduler.add_job(
        _safe("run_security_scans", lambda: run_security_scans(SessionLocal)),
        "interval",
        hours=1,
        id="run_security_scans",
    )
    # Fenêtre de rappel de 24h (agents/planning/scheduled_jobs.py::_REMINDER_WINDOW) : un
    # tick toutes les 30 minutes suffit largement à détecter l'échéance à temps.
    scheduler.add_job(
        _safe("send_appointment_reminders", lambda: send_appointment_reminders(SessionLocal)),
        "interval",
        minutes=30,
        id="send_appointment_reminders",
    )
    # Suivi des étapes de mise en place de l'offre ("office manager", extension de Planning) :
    # calculé à chaque tick à partir de l'état courant (Site/Post/Prospect/Backup), pas besoin
    # d'un tick plus fréquent que les autres jobs de suivi.
    scheduler.add_job(
        _safe("notify_onboarding_progress", lambda: notify_onboarding_progress(SessionLocal)),
        "interval",
        minutes=30,
        id="notify_onboarding_progress",
    )
    return scheduler
