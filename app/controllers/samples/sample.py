from flask import Blueprint
from flask import current_app
from flask import request
from datetime import datetime
import json

from bson.objectid import ObjectId
import requests
import pymongo
from flask_jwt_extended import jwt_required

logger = current_app.config["LOGGER"]
samples = Blueprint('samples', __name__, url_prefix='/api/v1/samples')
DB = current_app.config["DB"]
SAMPLES = DB["samples"]
DATASETS = DB["datasets"]

# Enable CORS
@samples.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    return response

@samples.route("", methods=['GET'])
@jwt_required()
def get_samples():
    logger.info("Getting datasets")
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
    
    columns = []
    for i in range(col_idx):
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

    # create the query
    search_criteria = {
        # "$or": [{ col["data"]: { "$regex": search, "$options": "i" } } for col in columns if col["searchable"] and col["data"] != None]
        "$and": [{ col["data"]: { "$regex": col["search_value"], "$options": "i" } } for col in columns if col["searchable"] and col["data"] != None and col["search_value"] != ""]
    }

    if search_criteria["$and"] == []:
        search_criteria = {}

    # Get the total number of records
    records_total = SAMPLES.count_documents({})
    records_filtered = SAMPLES.count_documents(search_criteria)

    # Get the data for the current page
    data = SAMPLES.find(search_criteria).skip(offset).limit(page_size)
    
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

@samples.route("", methods=['POST'])
@jwt_required()
def create_sample():
    logger.info("Creating sample")
    data = request.get_json()

    ref_dataset = data["ref_dataset"]
    language = data["language"]
    brands = data["brands"]

    # trim brands
    brands = [b.strip() for b in brands]
    details = data["details"]

    # GET DATASET INFO FROM MONGO
    ds = DATASETS.find_one({"_id": ObjectId(ref_dataset)})
    f_text = ds["features"]["text"]
    f_css = ds["features"]["css"]
    f_html = ds["features"]["html"]
    
    # ADD TO MONGO
    SAMPLES.insert_one({
        "ref_dataset": ds["_id"],
        "url": ds["url"],
        "brands": brands,
        "language": language,
        "details": details,
        "type": "valid_pish",
        "features": {
            "text": f_text,
            "css": f_css,
            "html": f_html
        },
        "screenshot": ds["screenshot"],
        "created_at": datetime.now(),
        "updated_at": None,
        "deleted_at": None
    })

    # get jwt token
    token = request.headers.get("Authorization").split(" ")[1]
    headers = {"Authorization": "Bearer " + token}

    # create api request to validate ds
    requests.post("http://localhost:8080/api/v1/datasets/" + ref_dataset, json={"status": "valid", "is_tweeted": True}, headers=headers)

    # convert to json
    return json.dumps({
        "status": "success",
        "data": "ok"
    })

@samples.route("/<sample_id>", methods=['GET'])
@jwt_required()
def get_sample(sample_id):
    sample = SAMPLES.find_one({"_id": ObjectId(sample_id)})
    return json.dumps({
        "status": "success",
        "data": sample
    })

@samples.route("/<sample_id>", methods=['PUT'])
@jwt_required()
def update_sample(sample_id):
    data = request.get_json()
    SAMPLES.update_one({"_id": ObjectId(sample_id)}, {"$set": {
        "brands": data["brands"],
        "language": data["language"] if data.get("language") != None else "en",
        "details": data["details"],
        "type": data["type"]
    }})

@samples.route("/<sample_id>", methods=['DELETE'])
@jwt_required()
def delete_sample(sample_id):
    # delete sampel
    SAMPLES.delete_one({"_id": ObjectId(sample_id)})
    return json.dumps({
        "status": "success",
        "data": None
    })

# delete mass
@samples.route("/delete_mass", methods=['POST'])
@jwt_required()
def delete_mass():
    data = request.get_json()
    for sample_id in data["ids"]:
        SAMPLES.delete_one({"_id": ObjectId(sample_id)})
    
    return json.dumps({
        "status": "success",
        "data": None
    })