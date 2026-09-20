from agents.creation_site.brief import Sector, SiteBrief
from agents.creation_site.content import ContentItem, SiteContent
from agents.creation_site.render import render_site


def _content() -> SiteContent:
    return SiteContent(
        hero_tagline="Bienvenue chez nous",
        hero_subtitle="Qualité et convivialité",
        about_text="Nous servons les meilleurs plats locaux.",
        items=[ContentItem(title="Poulet nyembwe", description="Plat traditionnel")],
        contact_intro="Venez nous voir",
    )


def test_render_restaurant_sector_uses_menu_label() -> None:
    brief = SiteBrief(
        business_name="Chez Awa", sector=Sector.restaurant, description="...", phone="+24101020304"
    )

    html = render_site(brief, _content())

    assert "Chez Awa" in html
    assert "Notre menu" in html
    assert "Poulet nyembwe" in html


def test_render_falls_back_to_generique_when_no_dedicated_template() -> None:
    # "artisanat" est dans le catalogue mais n'a pas encore de template dédié construit.
    brief = SiteBrief(
        business_name="Atelier Ebenisterie", sector=Sector.artisanat, description="...", phone="+24101020304"
    )

    html = render_site(brief, _content())

    assert "Nos services" in html
    assert "Atelier Ebenisterie" in html
