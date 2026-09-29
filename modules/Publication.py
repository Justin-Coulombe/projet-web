from datetime import date, datetime
from flask import request ,render_template, redirect, make_response, Blueprint
from Database import bd

Bp_publication = Blueprint('publications', __name__)


@Bp_publication.route('/', methods=['GET'])
def index():
    """
    Affiche une page pour afficher toutes les publications sur le site
    """
    all_publications = bd.get_all_publications()
    context = {'publications': all_publications}
    print(all_publications)
    return render_template('publications/index.jinja', context=context)


@Bp_publication.route('/recherche', methods=['GET'])
def research():
    """
    Affiche une page pour afficher toutes les publications sur le site
    """
    return render_template('publications/recherche.jinja')

        