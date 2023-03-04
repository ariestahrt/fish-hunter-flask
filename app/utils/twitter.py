import tweepy
from tweepy import API
from flask import current_app

TWITTER_CONSUMER_KEY=current_app.config["TWITTER_CONSUMER_KEY"]
TWITTER_CONSUMER_SECRET=current_app.config["TWITTER_CONSUMER_SECRET"]
TWITTER_ACCESS_TOKEN=current_app.config["TWITTER_ACCESS_TOKEN"]
TWITTER_SECRET_TOKEN=current_app.config["TWITTER_SECRET_TOKEN"]

def tweet(text, image_path):
    auth = tweepy.OAuth1UserHandler(
        TWITTER_CONSUMER_KEY,
        TWITTER_CONSUMER_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_SECRET_TOKEN
    )

    client = tweepy.Client(
        consumer_key=TWITTER_CONSUMER_KEY,
        consumer_secret=TWITTER_CONSUMER_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_SECRET_TOKEN
    )

    api = tweepy.API(auth)

    media = api.media_upload(filename=image_path)

    response = client.create_tweet(
        text=text,
        media_ids=[media.media_id_string]
    )
    return response