
"""Pages de publications; les filtres cartographiques AJAX sont traités par /api/publications/map."""

from flask import Blueprint, render_template, request, abort
from app.database.queries.publications import get_all_publications
from app.routes.api import paginate_data as paginate

Bp_publication = Blueprint('publications', __name__)


@Bp_publication.route('/', methods=['GET'])
def index():
    data = [p.to_dict() for p in get_all_publications()]
    per_page = 6

    page = request.args.get('page', default=1, type=int)
    pages = paginate(data, per_page)

    if page < 1 or page > max(1, len(pages)):
        abort(404)

    publications = pages[page - 1] if pages else []

    return render_template('publications/index.jinja', context={
        'publications': publications,
        'valid_time': True,
        'page_number': max(1, len(pages)),
        'active_page': page
    })


@Bp_publication.route('/recherche', methods=['GET'])
def research():
    return render_template('publications/recherche.jinja', context={
        'publications': [], 'publications_carte': [], 'valid_time': True
    })
