"""Rendu HTML statique d'un site à partir d'un brief et d'un contenu généré."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from agents.creation_site.brief import SiteBrief
from agents.creation_site.content import SiteContent

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=True)


def render_site(brief: SiteBrief, content: SiteContent) -> str:
    """Rend le site en une page HTML statique unique (index.html).

    Retombe sur le template générique si le secteur n'a pas encore de template dédié
    (seuls "restaurant" et "generique" sont construits à ce stade — catalogue complet dans
    agents/creation_site/skills/README.md, les 7 autres secteurs restent à designer).
    """
    template_name = f"sectors/{brief.sector.value}.html.jinja"
    try:
        template = _env.get_template(template_name)
    except TemplateNotFound:
        template = _env.get_template("sectors/generique.html.jinja")

    return template.render(brief=brief, content=content)
