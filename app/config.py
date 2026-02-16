import os


class BaseConfig:
    """Shared config for all environments"""

    SECRET_KEY = os.environ["SECRET_KEY"]
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    MONGO_URI = os.environ["MONGO_URI"]

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

    # Flask
    JSON_SORT_KEYS = False


class DevConfig(BaseConfig):
    """Local development"""

    DEBUG = True
    TESTING = False

    # Dev is fully writable
    MONGO_READ_ONLY = False


class StageConfig(BaseConfig):
    """Staging (Azure Cosmos DB)"""

    DEBUG = False
    TESTING = False

    # 🔒 IMPORTANT
    MONGO_READ_ONLY = True

    # Example Azure Cosmos Mongo API URI
    # mongodb://<user>:<password>@<account>.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb

