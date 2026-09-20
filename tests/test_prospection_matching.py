from agents.prospection.matching import normalize_business_name


def test_normalize_strips_accents_case_and_punctuation() -> None:
    assert normalize_business_name("Café de l'Étoile !") == "cafe de letoile"


def test_normalize_collapses_extra_whitespace() -> None:
    assert normalize_business_name("Chez   Awa  ") == "chez awa"


def test_normalize_is_stable_for_already_normalized_input() -> None:
    assert normalize_business_name("chez awa") == "chez awa"


def test_different_businesses_stay_distinct() -> None:
    assert normalize_business_name("Restaurant Awa") != normalize_business_name("Restaurant Awadi")
