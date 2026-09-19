# Modèle de coût unitaire par pack

Objectif : vérifier si les quotas chiffrés des 3 packs (CLAUDE.md §1) sont financièrement
tenables. Document de travail, à réviser avec des données d'usage réelles une fois l'app en
production (voir section "Ce qui reste inconnu").

## Tarifs connus (au 2026-09-19)

**API Claude** (tarifs officiels par million de tokens) :

| Modèle | Input | Output |
|---|---|---|
| Claude Sonnet 5 | 2,00 $ | 10,00 $ |
| Claude Haiku 4.5 | 1,00 $ | 5,00 $ |

**Cloudflare R2** : stockage ~0,015 $/Go/mois, pas de frais de sortie (egress). Coût
négligeable pour des sites statiques légers et des dumps PostgreSQL compressés.

**Fly.io** : coût d'infrastructure partagé (app + PostgreSQL), pas un coût marginal par
client à faible volume — à revisiter une fois le nombre de clients connu.

## Estimation du coût Claude API par action d'agent

Hypothèses de volumétrie de tokens par action (estimations de travail — à corriger avec des
mesures réelles `response.usage` une fois l'app en production, comme le recommande le
process standard d'optimisation de coûts API). Modèle utilisé par défaut : **Haiku 4.5**
pour les tâches de génération courtes/répétitives (posts, fiches prospect), **Sonnet 5**
pour les tâches nécessitant plus de qualité rédactionnelle (contenu de site, supports
d'offre) — choix de coût, à réévaluer si la qualité observée est insuffisante en pratique.

| Action | Modèle | Tokens (in/out, estimés) | Coût estimé |
|---|---|---|---|
| Génération complète d'un site | Sonnet 5 | 3 000 / 4 000 | ~0,05 $ |
| Révision de site | Sonnet 5 | 1 500 / 1 500 | ~0,02 $ |
| Post réseaux sociaux (texte + légende) | Haiku 4.5 | 500 / 300 | ~0,002 $ |
| Fiche prospect (extraction + structuration) | Haiku 4.5 | 1 000 / 500 | ~0,0035 $ |
| Support visuel d'offre (contenu texte) | Sonnet 5 | 800 / 600 | ~0,008 $ |

## Coût Claude API mensuel estimé par pack

En reprenant les quotas définis dans CLAUDE.md §1 (hypothèse d'usage moyen, pas le
plafond du quota pour les éléments "illimités") :

| | Starter | Business | Premium |
|---|---|---|---|
| Site (génération + révisions) | 1 génération + 2 révisions ≈ 0,09 $ | 1 génération + 4 révisions ≈ 0,13 $ | 1 génération + 8 révisions ≈ 0,21 $ |
| Réseaux sociaux (posts) | — | 12 posts ≈ 0,05 $ | 30 posts ≈ 0,12 $ |
| Prospection (fiches + supports) | — | 20 fiches + 1 support ≈ 0,15 $ | 60 fiches + 5 supports ≈ 0,46 $ |
| **Total Claude API estimé** | **≈ 0,09 $/mois** | **≈ 0,33 $/mois** | **≈ 0,79 $/mois** |

## Conclusion

**Le coût de l'API Claude n'est pas le facteur limitant** pour la viabilité des packs —
même pour Premium, il reste sous 1 $/mois/client, très en dessous de tout prix
d'abonnement plausible pour ce marché. **Les quotas définis dans CLAUDE.md §1 sont donc
validés du point de vue du coût Claude API.**

Les vrais leviers de coût à surveiller sont ailleurs :
- **WhatsApp Business API** : tarification à la conversation, variable selon le pays et la
  catégorie de message — **inconnue pour le Gabon**, à obtenir avant de fixer le prix final.
- **Google Places API** (si utilisée par l'agent Prospection pour la recherche) : facturée
  à la requête, potentiellement plus significative à volume élevé sur le pack Premium (60
  fiches/mois) — à chiffrer une fois l'intégration précisée.
- **Infrastructure** (Fly.io, R2) : coût partagé entre tous les clients, pas un coût
  marginal linéaire par client à ce stade — à revisiter une fois un volume de clients réel
  connu.
- **Temps humain** (support, onboarding, validation des contenus sensibles) : coût réel non
  capturé par ce modèle, à budgéter séparément.

## Ce qui reste inconnu (pas une décision technique, nécessite des données réelles)

- Tarification WhatsApp Business API par conversation au Gabon.
- Coût réel de l'intégration Google Places API selon le volume de requêtes de l'agent
  Prospection.
- Prix d'abonnement final par pack (en FCFA) — décision commerciale, pas technique.
- Mesure réelle des tokens consommés par action une fois l'app en production (ces
  estimations doivent être recalibrées avec `response.usage` réel, pas seulement supposées).
