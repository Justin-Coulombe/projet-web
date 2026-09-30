from flask import request, render_template, Blueprint

Bp_recherche = Blueprint("Recherche", __name__)


@Bp_recherche.route("", methods=["GET", "POST"])
def index():
    """
    Affiche une page de recherche avec des recommandations si la
    méthode est GET. Affiche une page avec les résultats de la recherche.
    """

    if request.method == "POST":
        # ville = request.form.get('ville', type=str)
        # date_debut = request.form.get('debut', type=date)
        # date_fin = request.form.get('fin', type=date)

        # envoie à la bd

        return render_template(
            "Recherche/index.jinja",
            element="hello POST"
        )

    return render_template(
        "Recherche/index.jinja",
        element="Hello GET"
    )