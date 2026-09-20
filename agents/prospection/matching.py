"""Rapprochement d'établissements entre sources de recherche (Google Places, Meta Pages).

Comble le point ouvert "rapprochement de sources au-delà du numéro de téléphone" — le même
établissement peut apparaître dans les deux sources sans numéro de téléphone commun (l'une
des deux ne l'a pas renseigné), auquel cas seul le nom permet de les rapprocher.

Décision délibérée : correspondance **exacte après normalisation**, pas de similarité floue
(distance de Levenshtein, etc.). Une correspondance floue introduirait des faux positifs
silencieux (fusionner deux établissements réellement différents, ex. deux restaurants au nom
proche mais distincts) — un risque plus grave qu'un doublon occasionnel non détecté, qui
reste visible et corrigible (deux fiches prospect au lieu d'une). La normalisation
elle-même (accents, casse, ponctuation) est le strict nécessaire pour absorber les écarts de
saisie triviaux entre deux API différentes, pas une tentative de rapprochement sémantique.
"""

import re
import unicodedata


def normalize_business_name(name: str) -> str:
    without_accents = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    lowercase = without_accents.lower()
    without_punctuation = re.sub(r"[^\w\s]", "", lowercase)
    return re.sub(r"\s+", " ", without_punctuation).strip()
