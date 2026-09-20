from agents.prospection.scoring import ProspectSignals, ScoringWeights, WebsiteStatus, score_prospect
from platform_core.models import ProspectCategory


def test_no_valid_contact_is_non_joignable_regardless_of_other_signals() -> None:
    signals = ProspectSignals(
        has_valid_contact=False,
        website_status=WebsiteStatus.none,
        sector_matches_catalog=True,
        has_recent_activity_signal=True,
    )

    category, score = score_prospect(signals)

    assert category == ProspectCategory.non_joignable
    assert score == 0


def test_no_website_plus_sector_match_plus_activity_is_favorable() -> None:
    signals = ProspectSignals(
        has_valid_contact=True,
        website_status=WebsiteStatus.none,
        sector_matches_catalog=True,
        has_recent_activity_signal=True,
    )

    category, score = score_prospect(signals)

    assert category == ProspectCategory.favorable
    assert score == 3 + 2 + 1


def test_modern_website_pushes_toward_non_favorable() -> None:
    signals = ProspectSignals(
        has_valid_contact=True,
        website_status=WebsiteStatus.modern,
        sector_matches_catalog=False,
        has_recent_activity_signal=False,
    )

    category, _score = score_prospect(signals)

    assert category == ProspectCategory.non_favorable


def test_missing_activity_signal_alone_is_a_qualifier_not_rejected() -> None:
    # Un seuil "favorable" relevé isole la contribution du signal d'activité : sans lui, le
    # prospect retombe en "à qualifier" (donnée manquante), jamais en "non favorable"
    # (skills/README.md : absence de donnée n'est pas un rejet).
    weights = ScoringWeights(favorable_threshold=6)
    base_signals = {
        "has_valid_contact": True,
        "website_status": WebsiteStatus.none,
        "sector_matches_catalog": True,
    }

    category_with_activity, _ = score_prospect(
        ProspectSignals(**base_signals, has_recent_activity_signal=True), weights=weights
    )
    category_without_activity, score_without_activity = score_prospect(
        ProspectSignals(**base_signals, has_recent_activity_signal=False), weights=weights
    )

    assert category_with_activity == ProspectCategory.favorable
    assert category_without_activity == ProspectCategory.a_qualifier
    assert score_without_activity > weights.non_favorable_threshold


def test_thresholds_are_configurable_via_weights() -> None:
    signals = ProspectSignals(
        has_valid_contact=True,
        website_status=WebsiteStatus.outdated,
        sector_matches_catalog=False,
        has_recent_activity_signal=False,
    )
    strict_weights = ScoringWeights(favorable_threshold=10)

    category, _score = score_prospect(signals, weights=strict_weights)

    # Avec un seuil "favorable" relevé à 10, le même score de 3 ne suffit plus.
    assert category != ProspectCategory.favorable
