"""CRUD stationnements : validation stricte des données et des fichiers."""
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from xmlrpc.client import FastMarshaller
from flask import Blueprint, render_template, request, session, url_for, abort, redirect
from app.database.queries.reservations import *
from app.database.queries.publications import (
    ajouter_stationnement as db_ajouter_stationnement,
    get_publications_by_id, get_publication_coordinates,
    update_publication, update_image, delete_publication
)
from app.form_validation import valider_stationnement, lire_photo
from app.form_responses import fail, success
from app.routes.auth import login_required
from app.services.geocoding import valider_jeton
from app.services.reservation_manager import verifier_si_disponible

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

    data, errors = valider_stationnement(request.form, verifier_dates=False)
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
    data['adresse'],
    data['prix'],
    data['place'],
    data['ville'],
    data['emplacement'],
    nom,
    session['user_id'],
    position['latitude'],
    position['longitude']
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
        abort(404, 'Annonce introuvable.')
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

    try:
        update_publication(
            publication_id, data['adresse'], data['prix'], data['place'],
            data['ville'], data['emplacement'],
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
        abort(404, 'Annonce introuvable.')
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
        abort(404, 'Annonce introuvable.')
    try:
        delete_publication(publication_id, session['user_id'])
    except sqlite3.IntegrityError:
        return 'Impossible de supprimer : des réservations existent.', 409
    return success(url_for('detail.detail_profil', success='Annonce supprimée.'),
                   message='Annonce supprimée.')


@bp_stationnement.route('/detail/<int:publication_id>', methods=['GET', 'POST'])
def detail(publication_id):

    context = {}
    context['v_time'] = True
    publication = get_publications_by_id(publication_id)
    if publication is None:
        abort(404, 'Annonce introuvable.')

    print("hey server 1")
    if request.method == 'POST':
        print("hey server 2")
        form = request.form
        action = form.get('btn_submit')
        date_du = form.get('date_du')
        date_au = form.get('date_au')
        if action == 'verification':
            if not date_du or not date_au:
                context['v_time'] = True
                return render_template('stationnement/detail.jinja', publication=publication.to_dict(), context=context, form=form)

            v_time = valid_time(date_du, date_au)
            context['v_time'] = v_time
            if not v_time:  
                return render_template('stationnement/detail.jinja', publication=publication.to_dict(), context=context, form=form)                  
            
            est_dispo, message = verifier_si_disponible(publication_id,date_du, date_au)
            if est_dispo : 
                context['can_submit'] = est_dispo
                context['message'] = message
                return render_template('stationnement/detail.jinja', publication=publication.to_dict(), context=context, form=form)   
            else:
                context['can_submit'] = est_dispo
                context['message'] = message
                return render_template('stationnement/detail.jinja', publication=publication.to_dict(), context=context, form=form)   
        else:
            est_dispo, message = verifier_si_disponible(publication_id,date_du, date_au) 
            print(est_dispo)   
            if est_dispo and add_Reservation(session.get('user_id'),date_du, date_au, publication_id):
                return redirect("/")

            context['message'] = "Opération annulée: une érreur c'est produit"
            context['can_submit'] = False
            return render_template('stationnement/detail.jinja', publication=publication.to_dict(), context=context, form=form)

    form = {'date_du': request.args.get('debut', ''), 'date_au' : request.args.get('fin', '')}
    return render_template('stationnement/detail.jinja', publication=publication.to_dict(), context=context, form=form)


def valid_time(date_debut, date_fin):
    debut = datetime.fromisoformat(date_debut)
    fin = datetime.fromisoformat(date_fin)
    return fin > debut


