from types import SimpleNamespace

import pytest

from agents.creation_site.brief import Sector, SiteBrief
from agents.creation_site.content import ContentGenerationError, generate_content

VALID_PAYLOAD = """
{
  "hero_tagline": "Bienvenue chez Awa",
  "hero_subtitle": "Le meilleur de la cuisine locale",
  "about_text": "Un restaurant familial au coeur de Libreville, ouvert depuis 2015.",
  "items": [{"title": "Poulet nyembwe", "description": "Plat traditionnel gabonais"}],
  "contact_intro": "Venez nous rendre visite"
}
"""


class _FakeMessages:
    def __init__(self, text: str) -> None:
        self._text = text

    def create(self, **kwargs) -> SimpleNamespace:
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._text)])


class _FakeClient:
    def __init__(self, text: str) -> None:
        self.messages = _FakeMessages(text)


def _brief() -> SiteBrief:
    return SiteBrief(
        business_name="Chez Awa",
        sector=Sector.restaurant,
        description="Restaurant familial de cuisine gabonaise",
        phone="+24101020304",
    )


def test_generate_content_parses_valid_response() -> None:
    content = generate_content(_brief(), client=_FakeClient(VALID_PAYLOAD))

    assert content.hero_tagline == "Bienvenue chez Awa"
    assert content.items[0].title == "Poulet nyembwe"


def test_generate_content_raises_on_invalid_json() -> None:
    with pytest.raises(ContentGenerationError):
        generate_content(_brief(), client=_FakeClient("ceci n'est pas du JSON"))


def test_generate_content_raises_on_schema_mismatch() -> None:
    with pytest.raises(ContentGenerationError):
        generate_content(_brief(), client=_FakeClient('{"unexpected": "shape"}'))
