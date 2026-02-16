import os

from flask import Flask
from flasgger import Swagger
from flask_cors import CORS
from .config import DevConfig, StageConfig
from .extensions import jwt, bcrypt, mongo
from .routes.auth import auth_bp
from .routes.receipts import receipts_bp


def create_app():
    app = Flask(__name__)

#    app.config.from_object(Config)
    env = os.getenv("FLASK_ENV", "development")
    if env == "staging":
        app.config.from_object(StageConfig)
    else:
        app.config.from_object(DevConfig)

    # Swagger config
    app.config["SWAGGER"] = {
        "title": "Dishlab API",
        "uiversion": 3,
        "securityDefinitions": {
            "bearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using Bearer scheme. Example: 'Bearer <token>'",
            }
        },
    }

    Swagger(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"].split(",")}})

    jwt.init_app(app)
    bcrypt.init_app(app)
    mongo.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(receipts_bp, url_prefix="/api/receipts")

    return app
