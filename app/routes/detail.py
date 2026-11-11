from flask import (
    Blueprint,
    render_template,
    session,
    request
)

from app.routes.auth import login_required
from app.database.queries.publications import get_publications_by_user
from app.database.queries.reservations import (
    get_reservation_by_user,
    get_reservations_by_owner
)

bp_detail = Blueprint("detail", __name__)


@bp_detail.route("/detail")
@login_required
def detail_profil():
    """Affiche le tableau de bord de l'utilisateur."""

    success = request.args.get("success")

    lst_pubications = get_publications_by_user(session['user_id'])
    lst_reversations = get_reservation_by_user(session['user_id'])

    return render_template(
        "profile/detail.jinja",
        success=success,
        lst_pubications=lst_pubications,
        lst_reversations=lst_reversations
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