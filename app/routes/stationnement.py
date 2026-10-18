from flask import Blueprint, render_template, redirect, url_for, request, session, current_app
from app.database.queries.publications import ajouter_stationnement as db_ajouter_stationnement
from app.database.queries.publications import get_publications_by_id, update_publication, update_image, delete_publication
from app.routes.auth import login_required
from app.services.geocoding import valider_jeton
from app.database.queries.publications import get_publication_coordinates

import os
import time
import logging


bp_stationnement = Blueprint('stationnement', __name__)

current_logger = logging.getLogger(__name__)


@bp_stationnement.route('/ajouter', methods=["GET", "POST"])
@login_required
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
        return render_template(
            'stationnement/ajouter.jinja',
            Entete="Ajouter un stationnement"
        )

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

    fichier = request.files.get('image')

    if not fichier or fichier.filename == "":
        message_image = "Assurez-vous de bien téléverser votre image"
        classe_image = "is-invalid"
        erreur = True

        # Vérifier que l'adresse a réellement été géolocalisée.
    jeton = request.form.get("geocode_token", "")

    position = valider_jeton(
        jeton,
        adresse,
        ville
    )

    msg_position = ""

    if position is None:
        erreur = True
        msg_position = (
            "Vous devez vérifier votre adresse avant "
            "de publier le stationnement."
        )

    if erreur:
        return render_template(
            'stationnement/ajouter.jinja',
            adresse=adresse,
            classe_adresse=classe_adresse,
            msg_adresse=msg_adresse,
            prix=prix,
            classe_prix=classe_prix,
            msg_prix=msg_prix,
            place=place,
            classe_place=classe_place,
            msg_place=msg_place,
            debut=debut,
            classe_debut=classe_debut,
            msg_debut=msg_debut,
            fin=fin,
            classe_fin=classe_fin,
            msg_fin=msg_fin,
            ville=ville,
            classe_ville=classe_ville,
            msg_ville=msg_ville,
            emplacement=emplacement,
            classe_emplacement=classe_emplacement,
            msg_emplacement=msg_emplacement,
            message_image=message_image,
            classe_image=classe_image,
            msg_position=msg_position
        )

    chemin_images = os.path.join(
        current_app.static_folder,
        "img",
        "stationnement"
    )

    os.makedirs(
        chemin_images,
        exist_ok=True
    )

    nom_image = (
        str(int(time.time() * 1000))
        + os.path.splitext(fichier.filename)[1]
    )

    chemin_complet = os.path.join(
        chemin_images,
        nom_image
    )

    fichier.save(chemin_complet)

    user_id = session["user_id"]


    db_ajouter_stationnement(
        adresse,
        prix,
        place,
        place,
        debut,
        fin,
        ville,
        emplacement,
        nom_image,
        user_id,
        position["latitude"],
        position["longitude"]
    )


    current_logger.info("Stationnement ajouté avec succès")

    return redirect(
        url_for('index'),
        code=303
    )


@bp_stationnement.route('/edit/<int:publication_id>', methods=["GET", "POST"])
@login_required
def edit(publication_id):
    """Permet au créateur d'un stationnement de le modifier"""

    publication = get_publications_by_id(publication_id)

    if publication is None:
        return redirect(url_for('index'), code=303)

    if publication.author_id != session['user_id']:
        return redirect(url_for('index'), code=303)

    if not publication_id:
        print("L'ID est manquant")

    if request.method == 'GET':
        success = request.args.get("success")
        img_success = request.args.get("img_success")
        return render_template('stationnement/edit.jinja', publication=publication, success=success, img_success=img_success)

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

    erreur = False

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


    adresse_modifiee = (
        (adresse or "").strip() != publication.address.strip()
        or (ville or "").strip() != publication.city.strip()
    )

    ancienne_position = get_publication_coordinates(publication_id)

    position_manquante = (
        ancienne_position is None
        or ancienne_position[0] is None
        or ancienne_position[1] is None
    )

    position = None
    msg_position = ""

    if adresse_modifiee or position_manquante:
        position = valider_jeton(
            request.form.get("geocode_token", ""),
            adresse,
            ville
        )

        if position is None:
            erreur = True
            msg_position = (
                "Vérifiez la nouvelle adresse avant "
                "d'enregistrer les modifications."
            )


    if erreur:
        return render_template(
            'stationnement/edit.jinja',
            publication=publication,
            adresse=adresse,
            classe_adresse=classe_adresse,
            msg_position=msg_position,
            msg_adresse=msg_adresse,
            prix=prix,
            classe_prix=classe_prix,
            msg_prix=msg_prix,
            place=place,
            classe_place=classe_place,
            msg_place=msg_place,
            debut=debut,
            classe_debut=classe_debut,
            msg_debut=msg_debut,
            fin=fin,
            classe_fin=classe_fin,
            msg_fin=msg_fin,
            ville=ville,
            classe_ville=classe_ville,
            msg_ville=msg_ville,
            emplacement=emplacement,
            classe_emplacement=classe_emplacement,
            msg_emplacement=msg_emplacement
        )

    update_publication(
        publication_id,
        adresse,
        prix,
        place,
        place,
        debut,
        fin,
        ville,
        emplacement,
        latitude=position["latitude"] if position else None,
        longitude=position["longitude"] if position else None
    )
    return redirect(url_for('stationnement.edit', publication_id=publication_id, success="Informations modifiées avec succès."), code=303)


@bp_stationnement.route('/edit/<int:publication_id>/image', methods=["POST"])
@login_required
def change_img(publication_id):
    """permet de modifier l'image d'un stationnement"""

    publication = get_publications_by_id(publication_id)

    fichier = request.files.get('image')
    erreur = False

    if publication is None or publication.author_id != session['user_id']:
        return redirect(url_for('index'), code=303)

    if not fichier or fichier.filename == "":
        erreur = True

    if request.method == 'GET':
        img_success = request.args.get("password_success")
        return render_template('stationnement/edit.jinja', publication=publication, img_success=img_success)

    if erreur:
        return render_template(
            'stationnement/edit.jinja',
            publication=publication,
            error="Assurez-vous de bien téléverser votre image"
        )

    chemin_images = os.path.join(
        current_app.static_folder,
        "img",
        "stationnement"
    )

    os.makedirs(
        chemin_images,
        exist_ok=True
    )

    nom_image = (
        str(int(time.time() * 1000))
        + os.path.splitext(fichier.filename)[1]
    )

    chemin_complet = os.path.join(
        chemin_images,
        nom_image
    )

    fichier.save(chemin_complet)

    if publication.img:
        ancien = os.path.join(chemin_images, publication.img)
        if os.path.exists(ancien):
            os.remove(ancien)

    update_image(publication_id, nom_image)

    return redirect(url_for('stationnement.edit', publication_id=publication_id, img_success="Image changer avec succès."), code=303)


@bp_stationnement.route("/supprimer/<int:publication_id>")
@login_required
def delete(publication_id):
    """Permet au créateur d'un stationnement de le modifier"""

    publication = get_publications_by_id(publication_id)

    if publication is None:
        return redirect(url_for('index'), code=303)

    if publication.author_id != session['user_id']:
        return redirect(url_for('index'), code=303)

    delete_publication(publication_id, session['user_id'])

    return redirect(url_for('detail.detail_profil', success="Annonces supprimée avec succés"), code=303)


@bp_stationnement.route('/detail/<int:publication_id>')
def detail(publication_id):
    """Permet de voir les detail d'une publication"""

    publication = get_publications_by_id(publication_id)

    if publication is None:
        return redirect(url_for('index'), code=303)


    if not publication_id:
        print("L'ID est manquant")

    return render_template('stationnement/detail.jinja', publication=publication)
