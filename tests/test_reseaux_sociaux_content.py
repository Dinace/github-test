from types import SimpleNamespace

import pytest

from agents.reseaux_sociaux.brief import PostBrief, PostObjective
from agents.reseaux_sociaux.content import ContentGenerationError, generate_content

VALID_PAYLOAD = """
{
  "caption": "Profitez de notre promotion exceptionnelle ce week-end !",
  "hashtags": ["promo", "gabon"]
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


def _brief() -> PostBrief:
    return PostBrief(objective=PostObjective.promotion, mandatory_elements=["Prix : 5000 FCFA"])


def test_generate_content_parses_valid_response() -> None:
    content = generate_content(_brief(), "chaleureux et familial", client=_FakeClient(VALID_PAYLOAD))

    assert "promotion" in content.caption.lower()
    assert content.hashtags == ["promo", "gabon"]


def test_generate_content_raises_on_invalid_json() -> None:
    with pytest.raises(ContentGenerationError):
        generate_content(_brief(), None, client=_FakeClient("pas du JSON"))


def test_generate_content_raises_on_schema_mismatch() -> None:
    with pytest.raises(ContentGenerationError):
        generate_content(_brief(), None, client=_FakeClient('{"unexpected": true}'))


def test_generate_content_works_without_brand_voice() -> None:
    content = generate_content(_brief(), None, client=_FakeClient(VALID_PAYLOAD))

    assert content.caption
