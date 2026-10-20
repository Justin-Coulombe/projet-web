from datetime import datetime, timezone

from flask import Blueprint, request, jsonify


Bp_api = Blueprint("API", __name__)


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
        

