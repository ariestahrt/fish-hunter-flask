import os

from flask import Flask
from flask_cors import CORS
from config import Config
import logging
import sys
from colargulog import ColorizedArgsFormatter
from colargulog import BraceFormatStyleFormatter
from flask_jwt_extended import JWTManager

def init_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    logging.getLogger("requests").propagate = False

    console_level = "INFO"
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(console_level)
    console_format = "%(asctime)s :: %(levelname)-8s :: %(message)s"
    colored_formatter = ColorizedArgsFormatter(console_format)
    console_handler.setFormatter(colored_formatter)
    root_logger.addHandler(console_handler)

init_logging()
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    logger.info("Starting app")

    # flask with https
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    jwt = JWTManager(app)
    app.config.from_mapping(
        LOGGER=logger
    )
    app.config.from_object(config_class)
    app.app_context().push()

    # home page
    @app.route('/')
    def index():
        return "Alive!"

    # register blueprints
    from app.controllers.datasets import dataset
    app.register_blueprint(dataset.datasets)
    from app.controllers.samples import sample
    app.register_blueprint(sample.samples)
    from app.controllers.chrome_api import chrome_api
    app.register_blueprint(chrome_api.chrome_api)
    from app.controllers.legits import legits
    app.register_blueprint(legits.legits)

    return app
