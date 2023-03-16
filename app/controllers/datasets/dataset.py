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
datasets = Blueprint('datasets', __name__, url_prefix='/api/v1/datasets')
DB = current_app.config["DB"]
DATASETS = DB["datasets"]
SAMPLES = DB["samples"]
MINIMUM_SCORE = float(current_app.config["MINIMUM_SCORE"])

# middleware
@datasets.before_request
def before_request():
    logger.info("Before request in datasets")
    # TODO: Implement JWT Check

@datasets.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    return "Hellow"

@datasets.route('/<ref_dataset>', methods=['POST'])
# @jwt_required()
def update_dataset(ref_dataset):
    logger.info("Validating dataset")
    data = request.get_json()
    status = data["status"]
    is_tweeted = data["is_tweeted"]

    # GET DATASET INFO FROM MONGO
    ds = DATASETS.find_one({"_id": ObjectId(ref_dataset)})

    # update dataset info
    DATASETS.update_one({"_id": ObjectId(ref_dataset)}, {
        "$set": {
            "status": status,
            "updated_at": datetime.now()
        }
    })

    if status == "valid" and is_tweeted:
        # tweet
        # setup brands tag
        brands_tag = ""
        for brand in ds["brands"]: brands_tag += f"#{brand} "

        tweetText = "New phishing colected!\n\n"
        tweetText += f"🔗 /{ds['domain_name']}/\n"
        tweetText += f"🆔 Brands: {brands_tag}\n"
        if ds["whois_domain_age"] != None:
            tweetText += f"📅 Domain age: {ds['whois_domain_age']}"
            if ds["whois_domain_age"] > 1:
                tweetText += " days\n"
            else:
                tweetText += " day\n"
        tweetText += f"🌐 IP: {ds['remote_ip_address']} ({ds['remote_ip_country_name']})\n"
        if ds["security_state"] == "secure":
            tweetText += f"🔐 SSL/TLS : {ds['security_protocol']} Issued By \"{ds['security_issuer']}\"\n"
        else:
            tweetText += "🔐 SSL/TLS : NO\n"
        tweetText += "\n#phishing #alert #scam #scampage"

        # download image
        img_data = requests.get(ds["screenshot"]["index"]).content
        temp_image_path = f"/tmp/{str(ds['_id'])}.jpg"
        with open(temp_image_path, 'wb') as handler:
            handler.write(img_data)

        tweetImage = temp_image_path
        tweet(tweetText, tweetImage)

    return json.dumps({
        "status": "success",
        "data": "ok"
    })

@datasets.route('/scan/<ref_dataset>/<validate>', methods=['GET'])
@jwt_required()
def scan_dataset(ref_dataset, validate):
    logger.info("Scanning dataset")
    ds = DATASETS.find_one({"_id": ObjectId(ref_dataset)})

    # get dataset features
    f_text = ds["features"]["text"]
    f_html = json.loads(ds["features"]["html"])
    f_css = json.loads(ds["features"]["css"])
    lang = ds["language"]

    # calculate similarity
    similarity_res = calculate_similarity(f_text, f_html, f_css, lang)

    if validate == "true":
        if similarity_res["final_score"] > MINIMUM_SCORE:
            # update dataset info
            requests.get(f"http://localhost:8080/api/v1/datasets/{ref_dataset}", json={
                "status": "valid",
                "is_tweeted": True
            })
    
    return json.dumps({
        "status": "success",
        "data": {
            "similarity": similarity_res
        }
    })

@datasets.route('/new_dt', methods=['GET'])
@jwt_required()
def new_dt():
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
    records_total = DATASETS.count_documents({})
    records_filtered = DATASETS.count_documents(search_criteria)

    # Get the data for the current page
    data = DATASETS.find(search_criteria, {'whois_lookup_text': 0}).skip(offset).limit(page_size)
    
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

@datasets.route('/<status>', methods=['GET'])
@jwt_required()
def get_datasets(status):
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
        "status": status,
        "$or": [{ col["data"]: { "$regex": search, "$options": "i" } } for col in columns if col["searchable"] and col["data"] != None]
    }

    # Get the total number of records
    records_total = DATASETS.count_documents({"status": status})
    records_filtered = DATASETS.count_documents(search_criteria)

    # Get the data for the current page
    data = DATASETS.find(search_criteria, {'whois_lookup_text': 0}).skip(offset).limit(page_size)
    
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