# Skills — Agent Maintenance

**Mission** : monitoring, sauvegardes, sécurité, détection de bugs sur les sites/comptes
clients.

**Périmètre** : lit/écrit uniquement les données de supervision (statuts, logs, backups) des
clients concernés. Ne touche jamais au code ou aux données d'un autre agent. Toute action
corrective non triviale (ex. restauration d'un backup) doit notifier un humain — voir
CLAUDE.md §5 ("notifier un humain en cas de décision sensible ou d'anomalie détectée").

## Skills / librairies retenues

| Skill | Rôle | Pourquoi ce choix |
|---|---|---|
| **Sentry** (`SENTRY_DSN`) | Remontée et agrégation des erreurs/bugs applicatifs en temps réel. | Standard de l'industrie, intégration Python mature, réduit le besoin de développer un système de tracking d'erreurs maison. |
| **UptimeRobot API** (`UPTIME_MONITOR_TOKEN`) | Surveillance de disponibilité des sites clients (uptime, temps de réponse). | Service managé simple à intégrer via API, évite d'opérer une infrastructure de monitoring dédiée dès le MVP. |
| **Sauvegardes planifiées** (variables `CLOUDFLARE_R2_*` + `pg_dump`/export de fichiers) | Sauvegarde régulière des données/sites clients vers Cloudflare R2. | `pg_dump` est l'outil standard pour PostgreSQL (cohérent avec le choix de base de données, CLAUDE.md §3) ; stockage sur R2 cohérent avec le choix d'hébergement (CLAUDE.md §3). |
| **Scan de sécurité basique** (ex. vérification d'en-têtes HTTP, dépendances obsolètes via `pip-audit`) | Détection de vulnérabilités simples sur les sites générés et le code de la plateforme. | Outils légers et open-source, suffisants pour un premier niveau de contrôle ; un scan plus poussé (type OWASP ZAP) pourra être ajouté plus tard si le besoin est confirmé. |
| **APScheduler** (`BackgroundScheduler`, `platform_core/scheduler.py`, partagé avec l'agent Réseaux sociaux et l'agent Planning) | Déclenche automatiquement sauvegardes/rétention, scans de sécurité et vérifications de disponibilité, à la place des appels manuels initiaux à l'API. | Préféré à Celery (envisagé initialement) : pas de broker externe (Redis/RabbitMQ) à opérer en plus pour une petite équipe qui démarre (CLAUDE.md §3, même logique que Fly.io/R2 vs AWS), suffisant pour des tâches périodiques dans le même process que l'app FastAPI. À réévaluer si le volume ou le besoin de distribuer les jobs sur plusieurs machines apparaît. |

## Politique de rétention des sauvegardes (tranché)

Rotation type grand-père/père/fils, alignée sur la fréquence déjà définie par pack
(CLAUDE.md §1), avec suppression automatique au-delà de la fenêtre pour maîtriser le coût
de stockage R2 :

| Pack | Fréquence | Rétention |
|---|---|---|
| Starter | Mensuelle | 3 dernières sauvegardes mensuelles (~3 mois) |
| Business | Hebdomadaire | 8 dernières sauvegardes hebdomadaires (~2 mois) + 3 derniers mois en mensuel dérivé |
| Premium | Quotidienne | 30 derniers jours + 12 dernières semaines (hebdo dérivé) + 6 derniers mois (mensuel dérivé) |

Toute restauration au-delà de cette fenêtre n'est pas possible (donnée supprimée) — à
communiquer clairement au client dans les conditions d'utilisation du pack.

## Seuils de notification humaine (tranché)

- **Site indisponible** : notification après 15 minutes consécutives d'indisponibilité (au
  lieu d'un seuil immédiat, pour absorber un simple aléa réseau ponctuel).
- **Erreur applicative répétée** (Sentry) : notification si la même erreur se répète ≥ 5
  fois en 1 heure (une occurrence isolée reste en log sans notification, pour éviter le
  bruit).
- **Échec d'une sauvegarde planifiée** : notification immédiate, systématique — un backup
  manqué est toujours critique et silencieux sinon.
- **Scan de sécurité** : vulnérabilité de sévérité haute/critique → notification immédiate ;
  sévérité faible/moyenne → regroupée dans un résumé hebdomadaire.

## Processus de restauration après incident (tranché)

1. L'agent identifie la sauvegarde valide la plus proche du point de restauration souhaité,
   dans la fenêtre de rétention ci-dessus.
2. L'agent **propose** la restauration à un humain (dashboard) — il ne l'exécute jamais de
   lui-même (cohérent avec l'interdiction CLAUDE.md §5 de supprimer/écraser des données
   client sans confirmation humaine, une restauration écrasant les données courantes).
3. Un humain confirme explicitement (action journalisée : qui, quand, quel point de
   restauration).
4. L'agent exécute la restauration seulement après cette confirmation, puis notifie le
   client concerné.

## Implémentation actuelle

- `backup.py` : `create_backup()` (pg_dump via subprocess, injectable), `upload_backup`/
  `list_backup_keys` (Cloudflare R2, réutilise `agents.creation_site.storage.get_r2_client`),
  et surtout `keys_to_retain(pack, keys, now)` — **implémentation réelle** de la rotation
  grand-père/père/fils du tableau ci-dessus (fonction pure, sans I/O, testée avec des
  historiques synthétiques de plusieurs mois). `apply_retention` supprime ce qui sort de la
  fenêtre calculée.
- `uptime.py` : `check_uptime` (API UptimeRobot, client HTTP injectable) et
  `should_notify_downtime` (seuil des 15 minutes, fonction pure).
- `security_scan.py` : `run_pip_audit` (sous-processus injectable, parsing best-effort —
  schéma JSON de `pip-audit` non revérifié contre la doc à jour dans cette session, voir
  note dans le fichier) et `classify_urgency` (répartition immédiat/résumé hebdo).
- `security_headers.py` : `check_security_headers(url)` — audit des en-têtes de sécurité
  HTTP (`Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`,
  `Content-Security-Policy`, `Referrer-Policy`) d'une URL **explicite**, et
  `classify_urgency` (même répartition immédiat/résumé hebdo que `security_scan.py`, seuil
  "haute" = `Strict-Transport-Security` manquant). Comble la **moitié** du point ouvert
  "scan de sécurité des sites clients générés eux-mêmes" — la logique d'audit, testable et
  utilisable dès maintenant, indépendamment de la question non tranchée de l'URL publique
  d'un site généré (`Site` n'a pas de champ URL, voir points ouverts). Exposé en
  déclenchement manuel (`POST /api/maintenance/security-scan/headers`, staff, prend l'URL
  en paramètre) — utilisable dès aujourd'hui sur n'importe quel site, y compris externe.
- `restore.py` : `propose_restore` / `confirm_restore` / `execute_restore` — implémente
  strictement le processus à 4 étapes ci-dessus ; `execute_restore` lève
  `RestoreNotConfirmedError` si appelé sur une demande qui n'est pas au statut `confirmed`,
  quelle que soit la façon dont il est invoqué (pas seulement une vérification côté API).
- **Sentry** : l'app elle-même est instrumentée (`app/main.py`, `sentry_sdk.init`), donc les
  erreurs réelles de la plateforme remontent dans Sentry. Le seuil "≥5 fois en 1h" **vit
  dans une règle d'alerte Sentry** (pas réimplémenté ici) ; `POST /api/maintenance/webhooks/
  sentry` reçoit cette alerte et crée une `Notification`. Signature HMAC-SHA256 du webhook
  vérifiée (`Sentry-Hook-Signature`, `SENTRY_WEBHOOK_SECRET`) — dégradée en no-op (comme
  avant) si le secret n'est pas configuré, comportement documenté et testé.
- Modèles ajoutés : `Notification` (catégorie/sévérité/statut), `Backup`, `RestoreRequest`.
- Endpoints (`app/routers/maintenance.py`), protégés par un jeton d'opération partagé —
  **stopgap explicite**, pas un vrai système d'auth staff (voir `app/auth.py::
  require_ops_token`) : lister/acquitter les notifications, déclencher une sauvegarde,
  proposer/confirmer/exécuter une restauration. Le webhook Sentry n'est volontairement pas
  derrière ce jeton (Sentry appelle directement, sans le connaître).
- Testé : rotation de rétention (les 3 packs, avec des dizaines de sauvegardes synthétiques
  étalées sur plusieurs mois), seuil de disponibilité, parsing pip-audit, audit des
  en-têtes de sécurité (présents/manquants, répartition immédiat/résumé hebdo, erreur
  réseau propagée), le refus d'exécuter une restauration non confirmée (le garde-fou
  central), et le flux complet via l'API — aucun appel réseau réel dans la suite de tests
  (Postgres, R2, UptimeRobot, Sentry tous simulés). `check_security_headers` a en plus été
  essayé une fois contre un vrai domaine externe (`example.com`) hors suite de tests : le
  sandbox bloque tout accès réseau sortant (politique d'organisation, pas un problème de
  credentials), mais ça a confirmé que la gestion d'erreur réseau fonctionne correctement
  en conditions réelles (`httpx.ProxyError` est bien un `httpx.HTTPError`, capturé et
  transformé en 502 par l'endpoint).
- `scheduled_jobs.py` : 3 tâches planifiées (APScheduler, voir `platform_core/scheduler.py`)
  remplaçant les déclenchements manuels ci-dessus.
  - `run_backups_and_retention` / `run_security_scans` : la sauvegarde (un seul `pg_dump` de
    toute la base) et le scan de sécurité (un seul `pip-audit` des dépendances de la
    plateforme) portent sur une ressource **partagée**, sans notion par client — décision
    actée dans cette session : leur cadence suit l'abonnement actif le plus exigeant
    (Premium > Business > Starter, ce dernier n'ayant pas de scan de sécurité du tout),
    calculée à chaque tick à partir du dernier `Backup`/de la dernière notification
    `security_finding` plutôt que fixée une fois pour toutes.
  - `run_uptime_checks` : par site (`Site.uptime_monitor_id`, `Site.last_uptime_check_at`,
    `Site.down_since` — 3 champs ajoutés, comblant l'ancien point ouvert), au rythme propre
    à l'abonnement actif du client (30 min/5 min/1 min, "temps réel" Premium approximé).
    Notifie une seule fois par période d'indisponibilité (pas de doublon à chaque tick tant
    que la précédente notification n'est pas acquittée).
- Le lifespan FastAPI (`app/main.py`) démarre le scheduler au lancement réel de l'app — pas
  pendant les tests, qui instancient `TestClient(app)` sans bloc `with` (vérifié
  explicitement : aucun job planifié ne tourne pendant la suite de tests).

## Points ouverts (pas encore fait, explicitement)

- **Vraie authentification staff** — le jeton d'opération partagé (`OPS_API_TOKEN`) n'est
  qu'un verrou minimal, pas un système avec comptes individuels/rôles/audit par utilisateur.
- Vérification de connectivité réelle : `pg_dump`/`psql` (Postgres), R2 et UptimeRobot n'ont
  jamais été exécutés contre de vrais services dans cette session (credentials non
  disponibles) — seule la logique est testée avec des doublures.
- Création automatique d'un monitor UptimeRobot à la publication d'un site — aujourd'hui
  `Site.uptime_monitor_id` doit être renseigné manuellement, sinon la tâche planifiée
  ignore ce site.
- Scan des en-têtes de sécurité **par site généré automatiquement** — `security_headers.py`
  fait le travail (voir "Implémentation actuelle"), mais reste un déclenchement manuel sur
  URL explicite : le brancher en tâche planifiée par site (comme `run_security_scans`)
  nécessite un schéma d'URL publique pour `Site`, qui n'existe pas encore (décision de
  modélisation plus large, non tranchée — voir MEMORY.md). Bloque aussi la création
  automatique de monitor UptimeRobot ci-dessus, même cause.

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : surveiller, sauvegarder, détecter des anomalies, notifier un humain.
- Interdit : supprimer des données client sans confirmation humaine, modifier le
  code/les données d'un autre agent, utiliser une clé API en dehors de
  `config/credentials/`.
