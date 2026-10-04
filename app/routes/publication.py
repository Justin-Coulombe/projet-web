
from datetime import datetime, timezone
from flask import Blueprint, render_template, request
from app.database.queries.publications import get_all_publications, get_publications_with_city_date_location_location

PATTERN = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"
TIME_PATTERN = str("%Y-%m-%d %H:%M")

Bp_publication = Blueprint("publications", __name__)


@Bp_publication.route("/", methods=["GET"])
def index():
    """
    Affiche une page pour afficher toutes les publications sur le site.
    """

    all_publications = get_all_publications()

    context = {
        "publications": all_publications
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
    valid_time = True

    filters = ["Tous", "Intérieur", "Extérieur", "%"]

    # get les paramètres de recherche s'il y en a
    city = request.args.get('city', "%")
    if city == "":
        city = "%"

    start = request.args.get('start', type=str, default="1970-01-01T00:00")
    if start == "":
        start = "1970-01-01 00:00"
    start = convert_time_string(start)

    end = request.args.get('end', type=str, default="3000-01-01T00:00")
    if end == "":
        end = "3000-01-01 00:00"
    end = convert_time_string(end)
    

    filter = request.args.get('filter', type=str, default="Tous")
    # filter validation 
    if filter == "" or filter == "Tous":
        filter = "%"

    valid_filter = filter in filters
    valid_time = validate_date_inputs(start, end)

    print(f"query validation info : \nfilter {valid_filter} \ntimes inputs {valid_time}")

    if(valid_time, valid_filter):
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

    if start_stamp > end_stamp:
        return False

    return True