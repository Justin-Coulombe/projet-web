"""API ParkShare : géocodage et recherche cartographique validés."""
import math
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.routes.auth import login_required
from app.form_validation import CITIES
from app.services.geocoding import trouver_coordonnees, creer_jeton, GeocodingIndisponible
from app.database.queries.publications import (
    get_publications_with_city_date_location_location, get_publications_in_bounds
)

Bp_api = Blueprint('API', __name__)


def _date(value):
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M')


@Bp_api.route('/publications/search')
def search_publication():
    city = request.args.get('city', '%')
    if city in ('', 'empt'):
        city = '%'
    if city != '%' and city not in CITIES:
        return jsonify(error='Ville invalide.'), 400
    filter_value = request.args.get('filter', '%')
    if filter_value in ('', 'Tous'):
        filter_value = '%'
    if filter_value not in ('%', 'Intérieur', 'Extérieur'):
        return jsonify(error='Type invalide.'), 400
    try:
        start = _date(request.args.get('start')) or '1970-01-01 00:00'
        end = _date(request.args.get('end')) or '3000-01-01 00:00'
        if start > end:
            raise ValueError()
    except ValueError:
        return jsonify(error='Dates invalides.'), 400
    rows = get_publications_with_city_date_location_location(
        {'city': city, 'start': start, 'end': end, 'filter': filter_value}
    )
    return jsonify([obj.to_dict() for obj in rows])


@Bp_api.route('/geocode', methods=['POST'])
@login_required
def verifier_adresse():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(ok=False, success=False, errors={'_form': 'JSON invalide.'}), 400
    adresse = payload.get('adresse')
    ville = payload.get('ville')
    if not isinstance(adresse, str) or not 5 <= len(adresse.strip()) <= 200:
        return jsonify(ok=False, success=False, message='Entrez une adresse valide.',
                       errors={'adresse': 'Entrez une adresse valide.'}), 400
    if not isinstance(ville, str) or ville.strip() not in CITIES:
        return jsonify(ok=False, success=False, message='Sélectionnez une ville valide.',
                       errors={'ville': 'Sélectionnez une ville valide.'}), 400
    adresse, ville = adresse.strip(), ville.strip()
    try:
        position = trouver_coordonnees(adresse, ville)
    except GeocodingIndisponible:
        return jsonify(ok=False, success=False, message='Géocodage indisponible, réessayez.'), 503
    if position is None:
        return jsonify(ok=False, success=False, message='Adresse non reconnue par OpenStreetMap.'), 422
    return jsonify(
        ok=True, success=True,
        adresse_complete=position['adresse_complete'],
        latitude=position['latitude'], longitude=position['longitude'],
        numero_exact=position.get('numero_exact', False),
        token=creer_jeton(adresse, ville, position)
    )


@Bp_api.route('/publications/map', methods=['GET'])
def publications_map():
    villes_autorisees = {
    "Montréal", "Québec", "Laval", "Gatineau",
    "Longueuil", "Sherbrooke", "Lévis", "Saguenay",
    "Trois-Rivières", "Terrebonne",
    "Saint-Jean-sur-Richelieu", "Brossard",
    "Repentigny", "Saint-Jérôme", "Drummondville"
    }

    ville = request.args.get("ville", "").strip()

    if ville and ville not in villes_autorisees:
        return jsonify({"error": "Ville invalide"}), 400
    
    try:
        south, north, west, east = (
            float(request.args[k]) for k in ('south', 'north', 'west', 'east')
        )
        if not all(math.isfinite(v) for v in (south, north, west, east)):
            raise ValueError()
        if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        return jsonify(error='Limites géographiques invalides.'), 400

    emplacement = request.args.get('filter', 'Tous')
    if emplacement not in {'Tous', 'Intérieur', 'Extérieur'}:
        return jsonify(error='Type de stationnement invalide.'), 400
    try:
        debut = _date(request.args.get('debut'))
        fin = _date(request.args.get('fin'))
        if debut and fin and debut > fin:
            raise ValueError()
    except ValueError:
        return jsonify(error='Dates de recherche invalides.'), 400
    return jsonify(get_publications_in_bounds(
        south=south, north=north, west=west, east=east,
        emplacement=emplacement, debut=debut, fin=fin,
        ville=ville or None
    ))


def paginate_data(data, perpage):
    sorted = []
    wrap = []

    if data == None:
        return []
    
    if len(data) <= perpage:
        for item in data:
            wrap.append(item)
        sorted.append(wrap)
    else:
        count = 0
        while count != len(data):
            wrap.append(data[count])
            count = count + 1
            if len(wrap) == perpage:
                sorted.append(wrap)
                wrap = [] 
            elif count == len(data):
                sorted.append(wrap)

    return sorted