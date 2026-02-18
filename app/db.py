from pymongo import MongoClient
from app.config import DevConfig, StageConfig
import os

_env = os.getenv("FLASK_ENV", "development")

settings = StageConfig() if _env == "staging" else DevConfig()

client = MongoClient(settings.MONGO_URI)
db = client.dishlab


def get_db():
    return db


def ensure_writable():
    if settings.MONGO_READ_ONLY:
        raise PermissionError("Read-only environment")
