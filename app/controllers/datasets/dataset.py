from flask import Blueprint
from flask import current_app
from flask import request
from datetime import datetime
import json

from bson.objectid import ObjectId
from app.utils.s3 import s3_download, s3_upload
from app.utils.sevenzip import extract_dataset
from app.utils.selenium_ss import screenshot
from app.utils.twitter import tweet

logger = current_app.config["LOGGER"]
datasets = Blueprint('datasets', __name__, url_prefix='/api/v1/datasets')
DB = current_app.config["DB"]
DATASETS = DB["datasets"]

@datasets.route("/test")
def test():
    print(current_app.config["SECRET_KEY"])
    return "Hello World"

@datasets.route('/<ref_dataset>', methods=['POST'])
def update_dataset(ref_dataset):
    logger.info("Validating dataset")
    data = request.get_json()
    status = data["status"]
    is_tweeted = data["is_tweeted"]

    # GET DATASET INFO FROM MONGO
    ds = DATASETS.find_one({"_id": ObjectId(ref_dataset)})

    # DOWNLOAD DATASET
    s3_path = ds["folder_path"] + ".7z"
    file_path = s3_download(s3_path)

    # extract dataset
    ds_path = extract_dataset(file_path)

    # screenshot
    index_path = "file://"+ds_path+"/index.html"
    screenshot_path = ds_path+"/screenshot.jpg"
    screenshot(index_path, screenshot_path)

    # upload screenshot to s3
    s3_upload("fh-ss-images", local_file=ds_path+"/screenshot.jpg", dest=f"valid_dataset/{str(ds['_id'])}.jpg")

    # update dataset info
    DATASETS.update_one({"_id": ObjectId(ref_dataset)}, {
        "$set": {
            "status": status,
            "screenshot_path": "https://fh-ss-images.s3.ap-southeast-1.amazonaws.com/valid_dataset/"+str(ds['_id'])+".jpg",
            "updated_at": datetime.now()
        }
    })

    # Tweet
    if is_tweeted:
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
        
        tweetImage = ds_path+"/screenshot.jpg"
        tweet(tweetText, tweetImage)

    return json.dumps({
        "status": "success",
        "data": "ok"
    })
