import pytest

from agents.prospection.compliance import ForbiddenSourceError, assert_source_allowed


def test_linkedin_is_blocked_with_no_exception() -> None:
    with pytest.raises(ForbiddenSourceError):
        assert_source_allowed("https://www.linkedin.com/company/example")


def test_linkedin_subdomain_is_also_blocked() -> None:
    with pytest.raises(ForbiddenSourceError):
        assert_source_allowed("https://fr.linkedin.com/in/someone")


def test_allowed_domain_passes() -> None:
    assert_source_allowed("https://www.chambre-commerce-gabon.example/annuaire")
