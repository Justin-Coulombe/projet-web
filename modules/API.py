from datetime import datetime, timezone
from sqlite3 import Date
from flask import request ,render_template, redirect, make_response, Blueprint, jsonify
from Database import bd

Bp_api = Blueprint('API', __name__)

@Bp_api.route('publications/search')
def search_publication():
    args = request.args
    city = args.get('city',"%")
    
    if city == 'empt':
        city = '%'

    start_date = datetime.fromtimestamp(float(args.get('start', "0"))/ 1000, timezone.utc).strftime('%Y-%m-%d %H:%M')
    end_date = datetime.fromtimestamp(float(args.get('end', "32503680000000")) / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
    params = {'city' : city, 'start' : start_date, 'end' : end_date}
    print(f'params = {params}')
    query_result = bd.get_publications_with_city_date(params)
    serialized = []
    for item in query_result:
        serialized.append(item.to_dict())

    return jsonify(serialized)