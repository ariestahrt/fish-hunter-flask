from flask import Blueprint
from flask import current_app
from flask import request
from datetime import datetime
import json
from datetime import datetime
from uuid import uuid4
from langdetect import detect

from bson.objectid import ObjectId
from app.utils.s3 import s3_download, s3_upload
from app.utils.sevenzip import extract_dataset
from app.utils.selenium_ss import screenshot
from app.utils.features_extractor import get_dataset_features
from app.utils.webpage_saver import save_webpage
from app.utils.similarity_calculator import calculate_similarity
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

    # generate eventid
    eventid = datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4())

    # TODO: Check if url is in whitelist
    
    # save the page
    temp_path = f"files/chrome-api/{eventid}/"
    save_webpage(url, html_content=html_dom, saved_path=temp_path)

    # TODO: Extract features from the website
    # extract features
    f_text, f_html, f_css = get_dataset_features(temp_path)
    # convert to object
    f_html = json.loads(f_html)
    f_css = json.loads(f_css)

    # detect language
    lang = detect(f_text)

    # Compare the features of the website with the features that we have in the database
    similarity_res = calculate_similarity(f_text, f_html, f_css, lang)

    return json.dumps({
        "status": "success",
        "data": {
            "eventid": eventid,
            "similarity": similarity_res
        }
    })