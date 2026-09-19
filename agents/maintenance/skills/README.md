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
| **Sauvegardes planifiées** (variables `CLOUDFLARE_R2_*` + `pg_dump`/export de fichiers + Celery beat) | Sauvegarde régulière des données/sites clients vers Cloudflare R2. | `pg_dump` est l'outil standard pour PostgreSQL (cohérent avec le choix de base de données, CLAUDE.md §3) ; planification via la même solution de tâches planifiées que l'agent Réseaux sociaux, pour mutualiser l'infrastructure ; stockage sur R2 cohérent avec le choix d'hébergement (CLAUDE.md §3). |
| **Scan de sécurité basique** (ex. vérification d'en-têtes HTTP, dépendances obsolètes via `pip-audit`) | Détection de vulnérabilités simples sur les sites générés et le code de la plateforme. | Outils légers et open-source, suffisants pour un premier niveau de contrôle ; un scan plus poussé (type OWASP ZAP) pourra être ajouté plus tard si le besoin est confirmé. |

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

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : surveiller, sauvegarder, détecter des anomalies, notifier un humain.
- Interdit : supprimer des données client sans confirmation humaine, modifier le
  code/les données d'un autre agent, utiliser une clé API en dehors de
  `config/credentials/`.
