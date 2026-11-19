from flask import (
    Blueprint,
    render_template,
    session,
    request,
    abort,
    url_for,
    redirect
    )

import os
import sqlite3
from app.form_responses import success
from app.routes.auth import login_required
from app.database.queries.publications import get_publications_by_user,get_publications_by_id
from app.database.queries.users import get_user_by_id
from app.database.queries.reservations import (
    get_reservation_by_user,
    get_reservations_by_owner,delete_reservation,update_reservation
)

bp_detail = Blueprint("detail", __name__)


@bp_detail.route("/detail")
@login_required
def detail_profil():
    """Affiche le tableau de bord de l'utilisateur."""

    success = request.args.get("success")
    lst_pubications = get_publications_by_user(session['user_id'])
    lst_reversations = get_reservation_by_user(session['user_id'])
    reservations = get_reservations_by_owner(session['user_id'])

    return render_template(
        "profile/detail.jinja",
        success=success,
        lst_pubications=lst_pubications,
        lst_reversations=lst_reversations,
        reservations=reservations
    )


@bp_detail.route("/reservations-recues", methods=["GET"])
@login_required
def reservations_recues():
    """Affiche les réservations reçues sur les stationnements du propriétaire."""

    owner_id = session['user_id']
    reservations = get_reservations_by_owner(owner_id)

    return render_template(
        "profile/reservations_recues.jinja",
        reservations=reservations
    )

@bp_detail.route("/reservations", methods=["GET"])
@login_required
def mes_reservations():
    """Affiche les réservations effectuées et reçues."""

    user_id = session["user_id"]

    lst_reversations = get_reservation_by_user(user_id)
    reservations = get_reservations_by_owner(user_id)

    return render_template(
        "profile/reservations.jinja",
        lst_reversations=lst_reversations,
        reservations=reservations
    )

@bp_detail.route('/supprimer/<int:reservation_id>', methods=['POST'])
@login_required
def delete(reservation_id):
    user_reservations = get_reservation_by_user(session['user_id'])
    if not any(r.id == reservation_id for r in user_reservations):
        abort(404, 'Réservation introuvable.')
    try:
        delete_reservation(reservation_id, session['user_id'])
    except sqlite3.IntegrityError:
        return 'Impossible de supprimer : des réservations existent.', 409
    return success(url_for('detail.detail_profil', success='Réservation supprimée.'),
                   message='Réservation supprimée.')


@bp_detail.route('/edit/<int:reservation_id>', methods=['GET', 'POST'])
@login_required
def edit(reservation_id):
    user_reservations = get_reservation_by_user(session['user_id'])
    reservation = None
    for r in user_reservations:
        if r.id == reservation_id:
            reservation = r

    if reservation is None:
        abort(404, 'Réservation introuvable.')

    publication = get_publications_by_id(reservation.post.id)
    if publication is None:
        abort(404, 'Stationnement introuvable.')

    if request.method == 'GET':
        return render_template('reservation/edit.jinja',
                               publication=publication,
                               reservation=reservation,
                               form={'date_du': reservation.start,
                                     'date_au': reservation.end})

    form = {
        'date_du': request.form.get('date_du', ''),
        'date_au': request.form.get('date_au', ''),
    }

    succes, message = update_reservation(
        reservation_id,
        session['user_id'],
        form['date_du'],
        form['date_au']
    )

    if succes:
        return redirect(url_for('detail.detail_profil',
                                success='Réservation modifiée.'))

    return render_template('reservation/edit.jinja',
                           publication=publication,
                           reservation=reservation,
                           error=message,
                           form=form)

@bp_detail.route('/client/<int:client_id>')
@login_required
def client(client_id):
    """Fiche publique d'un client"""
    client = get_user_by_id(client_id)
    if client is None:
        abort(404, 'Utilisateur introuvable.')

    return render_template('reservation/client.jinja', client=client)