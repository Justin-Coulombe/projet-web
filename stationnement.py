from flask import Blueprint, render_template, redirect, url_for, abort, request, session, Flask
from Database import bd
import utilitaire
import os,time
import re
import logging

bp_stationnement = Blueprint('stationnement', __name__)

app = Flask(__name__, static_url_path='')
app.logger.setLevel(logging.INFO)


app.config['ROUTE_VERS_AJOUTS'] = "/images/stationnement/"

app.config['CHEMIN_VERS_AJOUTS'] = os.path.join(
    app.instance_path.replace("instance", ""),
    "static",
    "images",
    "stationnement",
)


@bp_stationnement.route('/ajouter', methods=["GET", "POST"])
def ajouter_stationnement():
    """Ajouter une place de stationnement."""

    adresse = request.form.get('adresse')
    classe_adresse = ""
    msg_adresse = ""

    prix = request.form.get('prix')
    classe_prix = ""
    msg_prix = ""

    place = request.form.get('place')
    classe_place = ""
    msg_place = ""

    debut = request.form.get('dateDebut')
    classe_debut = ""
    msg_debut = ""

    fin = request.form.get('dateFin')
    classe_fin = ""
    msg_fin = ""

    ville = request.form.get('ville')
    classe_ville = ""
    msg_ville = ""

    emplacement = request.form.get('emplacement')
    classe_emplacement = ""
    msg_emplacement = ""


    message_image = ""
    classe_image = ""

    erreur = False

    if request.method == 'GET':
        return render_template('stationnement/ajouter.jinja', Entete="Ajouter un stationnement")

    if not adresse:
        classe_adresse = "is-invalid"
        msg_adresse = "Ce champ ne peut être vide"
        erreur = True

    if prix == "":
        classe_prix = "is-invalid"
        msg_prix = "Ce champ ne peut être vide"
        erreur = True

    if place == "":
        classe_place = "is-invalid"
        msg_place = "Ce champ ne peut être vide"
        erreur = True

    if not debut:
        classe_debut = "is-invalid"
        msg_debut = "Ce champ ne peut être vide"
        erreur = True

    if not fin:
        classe_fin = "is-invalid"
        msg_fin = "Ce champ ne peut être vide"
        erreur = True

    if not ville:
        classe_ville = "is-invalid"
        msg_ville = "Ce champ ne peut être vide"
        erreur = True

    if not emplacement:
        classe_emplacement = "is-invalid"
        msg_emplacement = "Ce champ ne peut être vide"
        erreur = True

    # fichier = request.files.get('image')
    fichier = request.files['image']
    if not fichier:
        message_image = "Assurez-vous de bien téléverser votre image"
        classe_image = "is-invalid"
        erreur = True

    os.makedirs(
        app.config['CHEMIN_VERS_AJOUTS'],
        exist_ok=True
    )

    nom_image = str(int(time.time())) + os.path.splitext(fichier.filename)[1]

    chemin_complet = os.path.join(
        app.config['CHEMIN_VERS_AJOUTS'],
        nom_image
    )

    fichier.save(chemin_complet)


    if erreur:
        return render_template(
            'stationnement/ajouter.jinja',
            Entete="Ajouter un stationnement",
            adresse=adresse,
            classe_adresse=classe_adresse,
            msg_adresse=msg_adresse, prix=prix, classe_prix=classe_prix, msg_prix=msg_prix, place=place, classe_place=classe_place, msg_place=msg_place, debut=debut, classe_debut=classe_debut, msg_debut=msg_debut, fin=fin, classe_fin=classe_fin, msg_fin=msg_fin, ville=ville, classe_ville=classe_ville, msg_ville=msg_ville, emplacement=emplacement, classe_emplacement=classe_emplacement, msg_emplacement=msg_emplacement, message_image=message_image,
            classe_image=classe_image, fichier=fichier
        )

    user_id = 1

    bd.ajouter_station(adresse, prix, place, debut, fin,
                       ville, emplacement, nom_image, user_id)
    app.logger.info("stationnement ajouter avec succés")
    return redirect(url_for('index'), code=303)
