from flask import Blueprint
from flask import current_app
from flask import request
from flask import jsonify
from datetime import datetime
import json, shutil, requests
import pymongo

from bson.objectid import ObjectId
from app.utils.twitter import tweet
from app.utils.similarity_calculator import calculate_similarity
from flask_jwt_extended import jwt_required

logger = current_app.config["LOGGER"]
legits = Blueprint('legits', __name__, url_prefix='/api/v1/legits')
DB = current_app.config["DB"]
LEGITS = DB["legit_datasets"]
SAMPLES = DB["samples"]
MINIMUM_SCORE = float(current_app.config["MINIMUM_SCORE"])

# Enable CORS
@legits.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    return response

# middleware
@legits.before_request
def before_request():
    logger.info("Before request in legits")
    # TODO: Implement JWT Check

@legits.route('', methods=['GET'])
@jwt_required()
def new_dt():
    logger.info("Getting legits")
    # Pagination parameters
    draw = int(request.args.get('draw'))
    page = int(request.args.get('page'))
    page_size = int(request.args.get('page_size'))

    search = request.args.get('search[value]')
    offset = (page - 1) * page_size

    # Get the columns
    col_idx = 0
    while True:
        if request.args.get(f'columns[{col_idx}][data]') == None:
            break
        col_idx += 1
    
    asset_criteria = None
    columns = []
    for i in range(col_idx):
        if request.args.get(f'columns[{i}][data]') == 'assets_downloaded':
            if request.args.get(f'columns[{i}][search][value]') != "":
                if request.args.get(f'columns[{i}][search][value]')[0] == ">":
                    asset_criteria = {
                        "operator": "$gte",
                        "value": float(request.args.get(f'columns[{i}][search][value]')[1:])
                    }
                elif request.args.get(f'columns[{i}][search][value]')[0] == "<":
                    asset_criteria = {
                        "operator": "$lte",
                        "value": float(request.args.get(f'columns[{i}][search][value]')[1:])
                    }
            continue

        columns.append({
            "data": request.args.get(f'columns[{i}][data]') if request.args.get(f'columns[{i}][data]') != "" else None,
            "name": request.args.get(f'columns[{i}][name]'),
            "searchable": True if request.args.get(f'columns[{i}][searchable]') == "true" else False,
            "orderable": True if request.args.get(f'columns[{i}][orderable]') == "true" else False,
            "search_value": request.args.get(f'columns[{i}][search][value]'),
            "search_regex": True if request.args.get(f'columns[{i}][search][regex]') == "true" else False,
        })

    # Get the order
    order_idx = 0
    while True:
        if request.args.get(f'order[{order_idx}][column]') == None:
            break
        order_idx += 1
    
    order = []
    for i in range(order_idx):
        order.append({
            "column": int(request.args.get(f'order[{i}][column]')),
            "dir": request.args.get(f'order[{i}][dir]')
        })
    
    search_criteria = {}
    # create the query
    if asset_criteria != None:
        search_criteria = {
            "assets_downloaded": {asset_criteria["operator"]: asset_criteria["value"]},
            # "$or": [{ col["data"]: { "$regex": search, "$options": "i" } } for col in columns if col["searchable"] and col["data"] != None]
            "$and": [{ col["data"]: { "$regex": col["search_value"], "$options": "i" } } for col in columns if col["searchable"] and col["data"] != None and col["search_value"] != ""]
        }
    else:
        search_criteria = {
            # "$or": [{ col["data"]: { "$regex": search, "$options": "i" } } for col in columns if col["searchable"] and col["data"] != None]
            "$and": [{ col["data"]: { "$regex": col["search_value"], "$options": "i" } } for col in columns if col["searchable"] and col["data"] != None and col["search_value"] != ""]
        }

    if search_criteria["$and"] == []:
        del search_criteria["$and"]

    # Get the total number of records
    records_total = LEGITS.count_documents({})
    records_filtered = LEGITS.count_documents(search_criteria)

    # Get the data for the current page
    data = LEGITS.find(search_criteria, {'whois_lookup_text': 0}).skip(offset).limit(page_size)
    
    # sort the data
    for o in order:
        data = data.sort(columns[o["column"]]["data"], pymongo.DESCENDING if o["dir"] == "desc" else pymongo.ASCENDING)

    # Create the response object
    response = {
        'data': list(data),
        'draw': draw,
        'recordsFiltered' : records_filtered,
        'recordsTotal': records_total,
    }

    return json.dumps(response, default=str)

@legits.route('/<ref_id>', methods=['GET'])
@jwt_required()
def get_legit(ref_id):
    logger.info("Getting legit")
    legit = LEGITS.find_one({"_id": ObjectId(ref_id)})
    return json.dumps(legit, default=str)

# Delete a legit
@legits.route('/<ref_id>', methods=['DELETE'])
@jwt_required()
def delete_legit(ref_id):
    logger.info("Deleting legit")
    LEGITS.delete_one({"_id": ObjectId(ref_id)})
    return json.dumps({
        "status": "success",
        "message": "Updated successfully",
        "data": "ok"
    })

# Update a legit
@legits.route('/<ref_id>', methods=['PUT'])
@jwt_required()
def update_legit(ref_id):
    logger.info("Updating legit")
    data = request.get_json()

    # Update the legit
    LEGITS.update_one({"_id": ObjectId(ref_id)}, {"$set": data})
    return json.dumps({
        "status": "success",
        "message": "Updated successfully",
        "data": "ok"
    })
