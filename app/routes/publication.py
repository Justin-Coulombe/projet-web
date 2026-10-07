
from datetime import datetime, timezone
from flask import Blueprint, render_template, request
from app.database.queries.publications import get_all_publications, get_publications_with_city_date_location_location
import re

PATTERN = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"
TIME_PATTERN = str("%Y-%m-%d %H:%M")
TIME_PATTERN_REG = r"%Y-%m-%dT%H:%M"
CITY_PATTERN = r"%|[^\W\d_]+(?:[ '-][^\W\d_]+)*"

Bp_publication = Blueprint("publications", __name__)


@Bp_publication.route("/", methods=["GET"])
def index():
    """
    Affiche une page pour afficher toutes les publications sur le site.
    """
    raw = get_all_publications()

    all_publications = []

    for pub in raw:
        all_publications.append(pub.to_dict())

    context = {
        "publications": all_publications,
        "valid_time": True
    }


    return render_template(
        "publications/index.jinja",
        context=context
    )


@Bp_publication.route("/recherche", methods=["GET"])
def research():
    """
    Affiche la page de recherche des publications.
    """
    context = {}
    valid_filter = False
    valid_time = False
    valid_city = False
    valid_params = True
    message = "Aucun résultat"

    filters = ["Tous", "Intérieur", "Extérieur", "%"]

    # get les paramètres de recherche s'il y en a
    city = request.args.get('ville', "%")
    if city == "":
        city = "%"
    
    valid_city = re.fullmatch(CITY_PATTERN, city.strip())
    if not valid_city:
        context['city_message'] = "Entrez un nom valide"
        context['valid_city'] = not valid_city

    start = request.args.get('debut', type=str, default="1970-01-01T00:00")
    if start == "":
        start = "1970-01-01 00:00"
    valid_params = re.fullmatch(PATTERN, start)
    start = convert_time_string(start)

    end = request.args.get('fin', type=str, default="3000-01-01T00:00")
    if end == "":
        end = "3000-01-01 00:00"
    valid_params = re.fullmatch(PATTERN, end)
    end = convert_time_string(end)
    

    filter = request.args.get('filter', type=str, default="Tous")
    # filter validation 
    if filter == "" or filter == "Tous":
        filter = "%"

    valid_filter = filter in filters    

    if not valid_params:
        message = "Paramètres invalide"
        valid_time = True
    else:
        valid_time = validate_date_inputs(start, end)

    print(f"valid time {valid_time}")
    if not valid_time:
        message_time = "La date ne doit pas être antérieur"
        context["time_message"] = message_time

    context["valid_time"] = valid_time

    context["message"] = message

    if(valid_time, valid_filter, valid_params):
        params = {"city": city, "start":start, "end":end, "filter":filter}
        raw = get_publications_with_city_date_location_location(params)
        publications = []

        for pub in raw:
            publications.append(pub.to_dict())
        context["publications"] = publications


    
    return render_template(
        "publications/recherche.jinja", context=context
    )

def convert_time_string(string):
    return string.replace('T', ' ')

def validate_date_inputs(start, end):
    start_time = datetime.strptime(start, TIME_PATTERN).replace(tzinfo=timezone.utc)
    end_time = datetime.strptime(end, TIME_PATTERN).replace(tzinfo=timezone.utc)

    start_stamp = start_time.timestamp()
    end_stamp = end_time.timestamp()

    print(f"les dates par defaut : \n{start_stamp}\n{end_stamp}")

    if start_stamp > end_stamp:
        return False

    return True