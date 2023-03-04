from flask import Blueprint
from flask import current_app
from flask import request
from datetime import datetime
import json, shutil

from bson.objectid import ObjectId
from app.utils.s3 import s3_download, s3_upload
from app.utils.sevenzip import extract_dataset
from app.utils.selenium_ss import screenshot
from app.utils.twitter import tweet
from app.utils.features_extractor import get_dataset_features
from app.utils.similarity import calculate_dict_similarity, lcs, ngram_similarity, NGramOri, cosine_similarity, calculate_by_lcs

logger = current_app.config["LOGGER"]
datasets = Blueprint('datasets', __name__, url_prefix='/api/v1/datasets')
DB = current_app.config["DB"]
DATASETS = DB["datasets"]
SAMPLES = DB["samples"]

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
    
    # remove extracted dataset
    shutil.rmtree(ds_path)

    return json.dumps({
        "status": "success",
        "data": "ok"
    })

@datasets.route('/scan/<ref_dataset>', methods=['GET'])
def scan_dataset(ref_dataset):
    logger.info("Scanning dataset")
    ds = DATASETS.find_one({"_id": ObjectId(ref_dataset)})

    # DOWNLOAD DATASET
    s3_path = ds["folder_path"] + ".7z"
    file_path = s3_download(s3_path)

    # extract dataset
    ds_path = extract_dataset(file_path)

    # get dataset features
    f_text, f_html, f_css = get_dataset_features(ds_path)
    # convert to object
    f_html = json.loads(f_html)
    f_css = json.loads(f_css)

    list_result = []

    # loop through samples
    list_samples = SAMPLES.find()
    for sample in list_samples:
        # get sample features
        sample_text = sample["features"]["text"]
        sample_html = json.loads(sample["features"]["html"])
        sample_css = json.loads(sample["features"]["css"])

        # compare features

        # CSS by cosine similarity
        css_score = calculate_dict_similarity(f_css, sample_css)

        # HTML By LCS
        lcs_res = lcs(f_html, sample_html)
        html_score = (2 * lcs_res[0]) / (len(f_html) + len(sample_html))

        # TEXT By
        # Calculate by using ngram=1
        by_ngram1 = ngram_similarity(f_text, sample_text, 1)

        # Calculate by ngram similarity
        by_ngram = NGramOri.compare(f_text, sample_text, N=1)

        # Calculate by cosine similarity
        by_cosine = cosine_similarity(f_text, sample_text)

        # Calculate by LCS
        by_lcs = calculate_by_lcs(f_text, sample_text)

        FINAL_CSS_SCORE = max(css_score[0], css_score[1])
        FINAL_HTML_SCORE = html_score
        FINAL_TEXT_SCORE = max(by_ngram, by_ngram1, by_cosine, by_lcs)

        FINAL_SCORE = FINAL_CSS_SCORE*0.4 + FINAL_HTML_SCORE*0.3 + FINAL_TEXT_SCORE*0.3

        list_result.append({
            "brands": sample["brands"],
            "ref_sample": str(sample["_id"]),
            "css_score": FINAL_CSS_SCORE,
            "html_score": FINAL_HTML_SCORE,
            "text_score": FINAL_TEXT_SCORE,
            "final_score": FINAL_SCORE,
        })