from flask import Blueprint
from flask import current_app
from flask import request
from datetime import datetime
import json

from bson.objectid import ObjectId
from app.utils.s3 import s3_download, s3_upload
from app.utils.sevenzip import extract_dataset
from app.utils.selenium_ss import screenshot
from app.utils.features_extractor import get_dataset_features
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

    # DOWNLOAD DATASET
    s3_path = ds["folder_path"] + ".7z"
    file_path = s3_download(s3_path)
    
    # EXTRACT DATASET
    ds_path = extract_dataset(file_path)

    # GET FEATURES
    f_text, f_html, f_css = get_dataset_features(ds_path)

    # SCREENSHOT
    index_path = "file://"+ds_path+"/index.html"
    screenshot_path = ds_path+"/screenshot.jpg"
    logger.info("Taking screenshot to {}", screenshot_path)
    screenshot(index_path, screenshot_path)

    # UPLOAD SCREENSHOT TO S3
    s3_upload("fh-ss-images", local_file=ds_path+"/screenshot.jpg", dest=f"valid_fish/{str(ds['_id'])}.jpg")
    
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
        "screenshot_path": "https://fh-ss-images.s3.ap-southeast-1.amazonaws.com/valid_fish/"+str(ds['_id'])+".jpg",
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