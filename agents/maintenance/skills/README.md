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
| **Sauvegardes planifiées** (`BACKUP_STORAGE_KEY` + `pg_dump`/export de fichiers + Celery beat) | Sauvegarde régulière des données/sites clients vers un stockage objet. | `pg_dump` est l'outil standard pour PostgreSQL (cohérent avec le choix de base de données, CLAUDE.md §3) ; planification via la même solution de tâches planifiées que l'agent Réseaux sociaux, pour mutualiser l'infrastructure. |
| **Scan de sécurité basique** (ex. vérification d'en-têtes HTTP, dépendances obsolètes via `pip-audit`) | Détection de vulnérabilités simples sur les sites générés et le code de la plateforme. | Outils légers et open-source, suffisants pour un premier niveau de contrôle ; un scan plus poussé (type OWASP ZAP) pourra être ajouté plus tard si le besoin est confirmé. |

## Points à trancher avant implémentation

- Fréquence des sauvegardes et politique de rétention (combien de versions conservées).
- Seuils déclenchant une notification humaine (ex. site down depuis X minutes, erreur
  critique répétée).
- Processus exact de restauration après incident (qui valide, comment).

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : surveiller, sauvegarder, détecter des anomalies, notifier un humain.
- Interdit : supprimer des données client sans confirmation humaine, modifier le
  code/les données d'un autre agent, utiliser une clé API en dehors de
  `config/credentials/`.
