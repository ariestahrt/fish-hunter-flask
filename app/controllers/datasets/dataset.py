from flask import Blueprint
from flask import current_app
from flask import request
from datetime import datetime
import json, shutil, requests

from bson.objectid import ObjectId
from app.utils.twitter import tweet
from app.utils.similarity_calculator import calculate_similarity

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

@datasets.route('/<ref_dataset>', methods=['POST'])
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
        img_data = requests.get(ds["screenshot_path"]).content
        temp_image_path = f"/tmp/{str(ds['_id'])}.jpg"
        with open(temp_image_path, 'wb') as handler:
            handler.write(img_data)

        tweetImage = temp_image_path
        tweet(tweetText, tweetImage)

    return json.dumps({
        "status": "success",
        "data": "ok"
    })

@datasets.route('/scan/<ref_dataset>', methods=['GET'])
def scan_dataset(ref_dataset):
    logger.info("Scanning dataset")
    ds = DATASETS.find_one({"_id": ObjectId(ref_dataset)})

    # get dataset features
    f_text = ds["features"]["text"]
    f_html = json.loads(ds["features"]["html"])
    f_css = json.loads(ds["features"]["css"])
    lang = ds["language"]

    # calculate similarity
    similarity_res = calculate_similarity(f_text, f_html, f_css, lang)

    if similarity_res["final_score"] > MINIMUM_SCORE:
        # update dataset info
        requests.get(f"http://localhost:8080/api/v1/datasets/{ref_dataset}", json={
            "status": "valid",
            "is_tweeted": True
        })
    
    return json.dumps({
        "status": "success",
        "data": "ok"
    })