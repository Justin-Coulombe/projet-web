from flask import Blueprint, render_template, redirect, url_for, abort, request

bp_station = Blueprint('station', __name__)


@bp_station.route('/ajouter', methods=["GET", "POST"])
def ajouter_station():
    """Ajouter une place de station."""
    adresse = request.form.get('adresse')
    classe_adresse = ""
    msg_adresse = ""
    erreur = False

    if request.method == 'GET':
        return render_template('station/ajouter.jinja', Entete="Ajouter une station")

    if adresse == "":
        classe_adresse = "is-invalid"
        msg_adresse = "Ce champ ne peut être vide"
        erreur = True

    if erreur:
        return render_template(
            'station/ajouter.jinja',
            Entete="Ajouter une station",
            adresse=adresse,
            classe_adresse=classe_adresse,
            msg_adresse=msg_adresse
        )
