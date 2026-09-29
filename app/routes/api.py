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

    start_date = datetime.fromtimestamp(
        float(args.get("start", "0")) / 1000,
        timezone.utc
    ).strftime("%Y-%m-%d %H:%M")

    end_date = datetime.fromtimestamp(
        float(args.get("end", "32503680000000")) / 1000,
        timezone.utc
    ).strftime("%Y-%m-%d %H:%M")

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