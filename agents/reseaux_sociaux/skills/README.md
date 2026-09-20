# Skills — Agent Réseaux sociaux

**Mission** : générer du contenu (textes, visuels), planifier un calendrier de publication,
et publier via les API des réseaux sociaux (Meta, WhatsApp Business) — uniquement sur
validation préalable d'un brief ou d'un contenu (voir CLAUDE.md §5, règle stricte : aucune
publication sans validation).

**Périmètre** : lit/écrit uniquement le contenu réseaux sociaux du client concerné. Ne
touche jamais au code ou aux données d'un autre agent.

## Skills / librairies retenues

| Skill | Rôle | Pourquoi ce choix |
|---|---|---|
| **Claude Agent SDK — génération de contenu** | Rédaction des textes de publication (posts, légendes, réponses type) adaptés au ton/secteur du client, à partir du brief. | Cohérent avec l'orchestration globale du projet ; permet de conditionner la génération à un brief structuré et de conserver la trace de ce qui a été généré/validé. |
| **Meta Graph API** (`META_ADS_TOKEN`, `META_APP_ID/SECRET`) | Publication et gestion de campagnes sur Facebook/Instagram. | API officielle, seule voie légitime pour publier au nom du client ; nécessaire pour respecter les conditions d'utilisation des plateformes. |
| **WhatsApp Business API** (`WHATSAPP_BUSINESS_TOKEN`) | Messages clients (confirmations, notifications), catalogue produit si applicable. | Canal de communication le plus utilisé par les PME/indépendants dans le marché cible ; API officielle obligatoire pour un usage professionnel conforme. |
| **APScheduler / Celery beat** | Planification du calendrier de publication (dates/heures programmées). | Solution standard en Python pour des tâches planifiées ; Celery beat si l'infrastructure prévoit déjà une file de tâches (ex. pour la Maintenance), sinon APScheduler pour un besoin plus léger. |
| **Pillow** (+ gabarits graphiques) | Génération de visuels simples (bannières, citations, promos) à partir d'un template de marque par client. | Suffisant pour des visuels basiques sans dépendance à un service tiers payant ; à réévaluer si un besoin de design plus avancé émerge (ex. API Canva). |

## Format du brief et workflow de validation (tranché)

**Brief structuré**, un objet par contenu prévu :
- objectif (ex. promotion, annonce, engagement) ;
- ton/voix — repris du profil de marque du client, défini une fois à l'onboarding ;
- éléments obligatoires (offre/prix/date si promo, mentions légales si nécessaire) ;
- visuel — généré par l'agent (Pillow) ou fourni par le client ;
- date/heure de publication souhaitée.

**Workflow de validation**, statuts successifs (aucun raccourci possible) :
1. `brouillon` — l'agent génère le contenu à partir du brief.
2. `en attente de validation` — le client est notifié (dashboard + WhatsApp).
3. `validé` — le client approuve tel quel, ou l'agent régénère après une demande de
   modification (retour à `brouillon`).
4. `planifié` puis `publié` — seul un contenu `validé` peut entrer dans la file de
   publication planifiée (APScheduler/Celery beat) ; la transition `validé` → `publié` est
   la seule qui déclenche un appel réel à l'API Meta/WhatsApp.

Traçabilité : chaque changement de statut (qui, quand, quoi) est stocké en base
(PostgreSQL) avec le contenu concerné — pas dans `MEMORY.md`, qui reste réservé au journal
de décisions techniques du projet, pas aux données clients.

## Portée initiale (tranché)

MVP : **Meta Graph API + WhatsApp Business API** uniquement (cohérent avec les packs
Business/Premium, CLAUDE.md §1). Google Business Profile reste rattaché à l'agent Création
de site (fiche établissement) ; Google Ads est différé après le MVP tant que la demande
n'est pas confirmée — la clé reste documentée dans `config/credentials/` sans être activée.

## Points à trancher avant implémentation

- Solution de génération de visuels plus avancée si Pillow s'avère insuffisant (à
  réévaluer sur retour d'usage réel, pas anticipé).

## Rappel des permissions (voir CLAUDE.md §5)

- Autorisé : générer du contenu à partir d'un brief, planifier des publications, publier
  **uniquement** si un brief ou une validation existe pour ce contenu précis.
- Interdit : publier sans validation préalable, modifier le code/les données d'un autre
  agent, utiliser une clé API en dehors de `config/credentials/`.
