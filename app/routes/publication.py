from flask import Blueprint, render_template

from app.database.queries.publications import get_all_publications


Bp_publication = Blueprint("publications", __name__)


@Bp_publication.route("/", methods=["GET"])
def index():
    """
    Affiche une page pour afficher toutes les publications sur le site.
    """

    all_publications = get_all_publications()

    context = {
        "publications": all_publications
    }

    return render_template(
        "publications/index.jinja",
        context=context
    )


@Bp_publication.route("/recherche", methods=["GET"])
def research():
    """
    Affiche la page de recherche des publications.
    """
    return render_template(
        "publications/recherche.jinja"
    )