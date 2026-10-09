from flask import (
    Blueprint,
    render_template,
    session,
)
from app.routes.auth import login_required
from app.database.queries.publications import get_publications_by_user
from app.database.queries.reservations import get_reservation_by_user

bp_detail = Blueprint("detail", __name__)


@bp_detail.route("/detail")
@login_required
def detail_profil():
    """Affiche le tableau de bords de l'utilisateur"""

    lst_pubications = get_publications_by_user(session['user_id'])
    lst_reversations = get_reservation_by_user(session['user_id'])

    return render_template("profile/detail.jinja", lst_pubications=lst_pubications,lst_reversations=lst_reversations)
