from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from pymongo import MongoClient

jwt = JWTManager()
bcrypt = Bcrypt()


class Mongo:
    def __init__(self):
        self.client = None
        self.read_only = False

    def init_app(self, app):
        self.read_only = app.config.get("MONGO_READ_ONLY", False)
        self.client = MongoClient(app.config["MONGO_URI"])
        app.extensions["mongo"] = self

    @property
    def db(self):
        return self.client.dishlab


mongo = Mongo()
