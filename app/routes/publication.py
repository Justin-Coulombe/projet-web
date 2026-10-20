"""Pages de publications; les filtres cartographiques AJAX sont traités par /api/publications/map."""
from flask import Blueprint, render_template
from app.database.queries.publications import get_all_publications

Bp_publication = Blueprint('publications', __name__)


@Bp_publication.route('/', methods=['GET'])
def index():
    return render_template('publications/index.jinja', context={
        'publications': [p.to_dict() for p in get_all_publications()],
        'valid_time': True
    })


@Bp_publication.route('/recherche', methods=['GET'])
def research():
    # La liste et la carte sont chargées via l'API et mises à jour sans recharge.
    return render_template('publications/recherche.jinja', context={
        'publications': [], 'publications_carte': [], 'valid_time': True
    })
