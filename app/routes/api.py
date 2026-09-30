from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from app.database.queries.publications import (
    get_publications_with_city_date
)


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


    query_result = get_publications_with_city_date(params)


    serialized = []

    for item in query_result:
        serialized.append(item.to_dict())

    return jsonify(serialized)

def convert_time_string(string):
    return string.replace('T', ' ')