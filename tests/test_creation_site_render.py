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


def test_render_boutique_sector_uses_produits_label() -> None:
    brief = SiteBrief(
        business_name="Boutique Bella", sector=Sector.boutique, description="...", phone="+24101020304"
    )

    html = render_site(brief, _content())

    assert "Nos produits" in html


def test_render_sante_sector_uses_specialites_label() -> None:
    brief = SiteBrief(
        business_name="Clinique du Centre", sector=Sector.sante, description="...", phone="+24101020304"
    )

    html = render_site(brief, _content())

    assert "Nos spécialités" in html


def test_all_catalogued_sectors_render_without_error() -> None:
    # Les 10 secteurs du catalogue (agents/creation_site/skills/README.md) ont désormais
    # tous un template dédié — ce test s'assure qu'aucun n'a été oublié ou cassé.
    for sector in Sector:
        brief = SiteBrief(
            business_name="Entreprise Test", sector=sector, description="...", phone="+24101020304"
        )

        html = render_site(brief, _content())

        assert "Entreprise Test" in html


def test_render_falls_back_to_generique_when_template_missing(monkeypatch) -> None:
    # Filet de sécurité : si un template de secteur venait à manquer (fichier supprimé par
    # erreur, nouveau secteur ajouté au catalogue avant son design), le rendu ne doit pas
    # planter — il retombe sur le template générique plutôt que de lever une exception.
    import agents.creation_site.render as render_module

    original_get_template = render_module._env.get_template

    def get_template_raising_for_restaurant(name: str, *args, **kwargs):
        if name == "sectors/restaurant.html.jinja":
            from jinja2 import TemplateNotFound

            raise TemplateNotFound(name)
        return original_get_template(name, *args, **kwargs)

    monkeypatch.setattr(render_module._env, "get_template", get_template_raising_for_restaurant)

    brief = SiteBrief(
        business_name="Chez Awa", sector=Sector.restaurant, description="...", phone="+24101020304"
    )

    html = render_site(brief, _content())

    assert "Nos services" in html  # label du template générique, pas "Notre menu"
