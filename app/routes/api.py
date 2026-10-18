from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from app.database.queries.publications import (
    get_publications_with_city_date_location_location
)

from flask import session
from app.routes.auth import login_required

from app.services.geocoding import (
    trouver_coordonnees,
    creer_jeton,
    GeocodingIndisponible
)
from datetime import datetime
from app.database.queries.publications import get_publications_in_bounds

Bp_api = Blueprint("API", __name__)


@Bp_api.route("/publications/search")
def search_publication():
    args = request.args

    city = args.get("city", "%")
    if city == "empt":
        city = "%"


    start_date = convert_time_string(args.get("start", "1970-01-01 00:00"))

    end_date = convert_time_string(args.get("end", "3000-01-01 00:00"))

    params = {
        "city": city,
        "start": start_date,
        "end": end_date
    }


    query_result = get_publications_with_city_date_location_location(params)


    serialized = []

    for item in query_result:
        serialized.append(item.to_dict())

    return jsonify(serialized)


@Bp_api.route("/geocode", methods=["POST"])
@login_required
def verifier_adresse():
    data = request.get_json(silent=True) or {}

    adresse = str(data.get("adresse") or "").strip()
    ville = str(data.get("ville") or "").strip()

    if not (5 <= len(adresse) <= 200):
        return jsonify({
            "success": False,
            "message": "Entrez une adresse valide."
        }), 400

    if not (2 <= len(ville) <= 100):
        return jsonify({
            "success": False,
            "message": "Sélectionnez une ville."
        }), 400

    try:
        position = trouver_coordonnees(adresse, ville)
    except GeocodingIndisponible:
        return jsonify({
            "success": False,
            "message": "Service de géocodage indisponible. Réessayez."
        }), 503

    if position is None:
        return jsonify({
            "success": False,
            "message": (
                "Adresse introuvable ou numéro civique non reconnu "
                "dans OpenStreetMap. Vérifiez l'adresse et la ville."
            )
        }), 422

    jeton = creer_jeton(adresse, ville, position)

    return jsonify({
        "success": True,
        "adresse_complete": position["adresse_complete"],
        "latitude": position["latitude"],
        "longitude": position["longitude"],
        "numero_exact": position["numero_exact"],
        "token": jeton
    })



@Bp_api.route("/publications/map", methods=["GET"])
def publications_map():
    try:
        south = float(request.args["south"])
        north = float(request.args["north"])
        west = float(request.args["west"])
        east = float(request.args["east"])

        if not (
            -90 <= south < north <= 90
            and -180 <= west < east <= 180
        ):
            return jsonify({"error": "Limites invalides"}), 400

    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Coordonnées invalides"}), 400

    emplacement = request.args.get("filter", "Tous")

    if emplacement not in ("Tous", "Intérieur", "Extérieur"):
        return jsonify({"error": "Filtre invalide"}), 400

    debut = request.args.get("debut") or None
    fin = request.args.get("fin") or None

    try:
        if debut:
            debut = datetime.strptime(
                debut, "%Y-%m-%dT%H:%M"
            ).strftime("%Y-%m-%d %H:%M")

        if fin:
            fin = datetime.strptime(
                fin, "%Y-%m-%dT%H:%M"
            ).strftime("%Y-%m-%d %H:%M")

        if debut and fin and debut > fin:
            return jsonify({
                "error": "La date de fin précède le début."
            }), 400

    except ValueError:
        return jsonify({"error": "Dates invalides"}), 400

    publications = get_publications_in_bounds(
        south=south,
        north=north,
        west=west,
        east=east,
        emplacement=emplacement,
        debut=debut,
        fin=fin
    )

    return jsonify(publications)