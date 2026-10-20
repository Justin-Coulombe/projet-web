"""CRUD stationnements : validation stricte des données et des fichiers."""
import logging
import os
import sqlite3
import uuid
from pathlib import Path
from flask import Blueprint, render_template, request, session, url_for
from app.database.queries.publications import (
    ajouter_stationnement as db_ajouter_stationnement,
    get_publications_by_id, get_publication_coordinates,
    update_publication, update_image, delete_publication
)
from app.form_validation import valider_stationnement, lire_photo
from app.form_responses import fail, success
from app.routes.auth import login_required
from app.services.geocoding import valider_jeton

bp_stationnement = Blueprint('stationnement', __name__)
logger = logging.getLogger(__name__)


def _repertoire_images():
    from flask import current_app
    chemin = Path(current_app.static_folder) / 'img' / 'stationnement'
    chemin.mkdir(parents=True, exist_ok=True)
    return chemin


def _sauver_photo(contenu):
    nom = f'{uuid.uuid4().hex}.jpg'
    chemin = _repertoire_images() / nom
    chemin.write_bytes(contenu)
    return nom, chemin


def _erreur_formulaire(errors, template, publication=None, **form):
    allowed = {k: v for k, v in form.items() if k in {
        'adresse', 'prix', 'place', 'ville', 'emplacement', 'debut', 'fin', 'dateDebut', 'dateFin'
    }}
    if publication is not None:
        return fail(errors, template, publication=publication, **allowed)
    return fail(errors, template, **allowed)


@bp_stationnement.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_stationnement():
    if request.method == 'GET':
        return render_template('stationnement/ajouter.jinja')

    data, errors = valider_stationnement(request.form)
    photo, photo_error = lire_photo(request.files.get('image'), obligatoire=True)
    if photo_error:
        errors['image'] = photo_error

    position = None
    if 'adresse' in data and 'ville' in data:
        position = valider_jeton(request.form.get('geocode_token'), data['adresse'], data['ville'])
    if position is None:
        errors['geocode_token'] = "Vérifiez l'adresse sur la carte avant de publier."

    if errors:
        return _erreur_formulaire(errors, 'stationnement/ajouter.jinja', **request.form.to_dict())

    nom = None
    chemin = None
    try:
        nom, chemin = _sauver_photo(photo)
        db_ajouter_stationnement(
            data['adresse'], data['prix'], data['place'], data['place'],
            data['debut'], data['fin'], data['ville'], data['emplacement'],
            nom, session['user_id'], position['latitude'], position['longitude']
        )
    except (sqlite3.Error, OSError):
        if chemin is not None:
            chemin.unlink(missing_ok=True)
        logger.exception('Échec création stationnement')
        return _erreur_formulaire({'_form': 'Impossible de publier pour le moment.'},
                                  'stationnement/ajouter.jinja', **request.form.to_dict())
    return success(url_for('detail.detail_profil'), message='Stationnement créé.')


@bp_stationnement.route('/edit/<int:publication_id>', methods=['GET', 'POST'])
@login_required
def edit(publication_id):
    publication = get_publications_by_id(publication_id)
    if publication is None or publication.author_id != session['user_id']:
        return 'Annonce introuvable.', 404
    if request.method == 'GET':
        coords = get_publication_coordinates(publication_id)
        return render_template('stationnement/edit.jinja', publication=publication,
            has_coordinates=bool(coords and coords[0] is not None and coords[1] is not None),
            success=request.args.get('success'), img_success=request.args.get('img_success'))

    data, errors = valider_stationnement(request.form)
    position = None
    if 'adresse' in data and 'ville' in data:
        modifiee = (data['adresse'] != publication.address.strip()
                    or data['ville'] != publication.city.strip())
        coords = get_publication_coordinates(publication_id)
        absente = not coords or coords[0] is None or coords[1] is None
        if modifiee or absente:
            position = valider_jeton(
                request.form.get('geocode_token'), data['adresse'], data['ville']
            )
            if position is None:
                errors['geocode_token'] = "Vérifiez la nouvelle adresse sur la carte."

    # Ne pas créer artificiellement des places libres si une réservation existe.
    if 'place' in data:
        occupees = max(0, publication.open_place - publication.place_use)
        if data['place'] < occupees:
            errors['place'] = f'Il y a déjà {occupees} réservation(s) actives.'
    if errors:
        return _erreur_formulaire(errors, 'stationnement/edit.jinja', publication, **request.form.to_dict())

    occupees = max(0, publication.open_place - publication.place_use)
    places_libres = data['place'] - occupees
    try:
        update_publication(
            publication_id, data['adresse'], data['prix'], data['place'],
            places_libres, data['debut'], data['fin'], data['ville'], data['emplacement'],
            latitude=position['latitude'] if position else None,
            longitude=position['longitude'] if position else None
        )
    except sqlite3.Error:
        logger.exception('Échec mise à jour stationnement')
        return _erreur_formulaire({'_form': 'Enregistrement impossible.'},
                                  'stationnement/edit.jinja', publication)
    return success(url_for('stationnement.edit', publication_id=publication_id,
                           success='Informations mises à jour.'), message='Annonce modifiée.')


@bp_stationnement.route('/edit/<int:publication_id>/image', methods=['POST'])
@login_required
def change_img(publication_id):
    publication = get_publications_by_id(publication_id)
    if publication is None or publication.author_id != session['user_id']:
        return 'Annonce introuvable.', 404
    photo, erreur = lire_photo(request.files.get('image'))
    if erreur:
        return _erreur_formulaire({'image': erreur}, 'stationnement/edit.jinja', publication)
    nom = None
    chemin = None
    try:
        nom, chemin = _sauver_photo(photo)
        update_image(publication_id, nom)
    except (sqlite3.Error, OSError):
        if chemin is not None:
            chemin.unlink(missing_ok=True)
        logger.exception('Erreur mise à jour photo')
        return _erreur_formulaire({'_form': 'Impossible de modifier la photo.'},
                                  'stationnement/edit.jinja', publication)
    if publication.img:
        # Nettoyer seulement dans le dossier prévu et après succès de l'UPDATE.
        try:
            ancien = _repertoire_images() / os.path.basename(publication.img)
            ancien.unlink(missing_ok=True)
        except OSError:
            logger.warning('Ancienne photo non supprimée', exc_info=True)
    return success(url_for('stationnement.edit', publication_id=publication_id,
                           img_success='Image modifiée.'), message='Photo modifiée.')


@bp_stationnement.route('/supprimer/<int:publication_id>', methods=['POST'])
@login_required
def delete(publication_id):
    publication = get_publications_by_id(publication_id)
    if publication is None or publication.author_id != session['user_id']:
        return 'Annonce introuvable.', 404
    try:
        delete_publication(publication_id, session['user_id'])
    except sqlite3.IntegrityError:
        return 'Impossible de supprimer : des réservations existent.', 409
    return success(url_for('detail.detail_profil', success='Annonce supprimée.'),
                   message='Annonce supprimée.')


@bp_stationnement.route('/detail/<int:publication_id>')
def detail(publication_id):
    publication = get_publications_by_id(publication_id)
    if publication is None:
        return 'Annonce introuvable.', 404
    return render_template('stationnement/detail.jinja', publication=publication)
