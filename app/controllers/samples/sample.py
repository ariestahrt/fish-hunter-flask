from flask import Blueprint
from flask import current_app
from flask import request
from datetime import datetime
import json

from bson.objectid import ObjectId
import requests

logger = current_app.config["LOGGER"]
samples = Blueprint('samples', __name__, url_prefix='/api/v1/samples')
DB = current_app.config["DB"]
SAMPLES = DB["samples"]
DATASETS = DB["datasets"]

@samples.route("", methods=['POST'])
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

    # create api request to validate ds
    requests.post("http://localhost:8080/api/v1/datasets/" + ref_dataset, json={"status": "valid", "is_tweeted": True})

    # convert to json
    return json.dumps({
        "status": "success",
        "data": "ok"
    })