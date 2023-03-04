import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGO_CLIENT = MongoClient(os.getenv("MONGO_CONNECTION_STRING"))

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = "dev"
    DB = MONGO_CLIENT['hunter']
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    ZIP_PASSWORD = os.getenv("7Z_PASSWORD")
    TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
    TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_SECRET_TOKEN = os.getenv("TWITTER_SECRET_TOKEN")