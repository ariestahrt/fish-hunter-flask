import json
from flask import current_app
from app.utils.similarity import calculate_dict_similarity, lcs, ngram_similarity, NGramOri, cosine_similarity, calculate_by_lcs

logger = current_app.config["LOGGER"]

MULTIPLIER_CSS = float(current_app.config["MULTIPLIER_CSS"])
MULTIPLIER_HTML = float(current_app.config["MULTIPLIER_HTML"])
MULTIPLIER_TEXT = float(current_app.config["MULTIPLIER_TEXT"])

DB = current_app.config["DB"]
SAMPLES = DB["samples"]

def calculate_similarity(f_text, f_html, f_css, lang):
    # get all samples with the same language
    list_samples = SAMPLES.find({"lang": lang})

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

        FINAL_SCORE = FINAL_CSS_SCORE*MULTIPLIER_CSS + FINAL_HTML_SCORE*MULTIPLIER_HTML + FINAL_TEXT_SCORE*MULTIPLIER_TEXT

        list_result.append({
            "brands": sample["brands"],
            "ref_sample": str(sample["_id"]),
            "css_score": FINAL_CSS_SCORE,
            "html_score": FINAL_HTML_SCORE,
            "text_score": FINAL_TEXT_SCORE,
            "final_score": FINAL_SCORE,
        })
    
    # sort result
    list_result = sorted(list_result, key=lambda k: k['final_score'], reverse=True)

    # print best result
    logger.info("Best result: {}".format(json.dumps(list_result[0], indent=4)))

    return list_result[0]
