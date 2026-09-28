from datetime import date, datetime
from flask import request ,render_template, redirect, make_response, Blueprint

Bp_recherche = Blueprint('Recherche', __name__)

@Bp_recherche.route('', methods=['GET', 'POST'])
def index():
    """
    Affiche une page de recherche avec des recommendation si la 
    methode est GET. Affiche une page avec les résultats de la recherche
    """
    context = {}
    if request.method == 'POST':
        # form = request.form
        # ville = form.get('ville', type=str)
        # date_debut = request.form.get('debut', type=date)
        # date_fin = form.get('fin', type=date)
        # envoie à la bd
        return render_template('Recherche/index', element="hello POST")

    context['resultats'] = _get_fake_result()
    context['arguments'] = 'faux arguments'
    context['nb_article'] = 3
    return render_template('recherche/index.jinja', element="Hello GET", context=context)

def _get_fake_result():
    item = {'prix': 22, 'address': '123 rue campagne', 'emplacement':'dehors'}
    resultat = []
    for i in range(2):
        resultat.append(item)

    return resultat
        