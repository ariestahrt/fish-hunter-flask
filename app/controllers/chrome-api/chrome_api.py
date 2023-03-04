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
chrome_api = Blueprint('chrome_api', __name__, url_prefix='/api/v1/chrome_api')
DB = current_app.config["DB"]
SAMPLES = DB["samples"]
DATASETS = DB["datasets"]

@chrome_api.route("/scan", methods=['POST'])
def scan():
    logger.info("Scanning website")
    data = request.get_json()

    url = data["url"]
    html_dom = data["html_dom"]

    # TODO: Check if url is in whitelist

    # TODO: Extract features from the website

    # TODO: Compare the features of the website with the features that we have in the database

    # TODO: If the website is similar to one of the websites in the database (similarity scores > 0.8), then return the dataset id