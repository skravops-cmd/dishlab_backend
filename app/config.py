import os
from pydantic import BaseSettings


class BaseConfig(BaseSettings):
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    MONGO_URI: str
    CORS_ORIGINS: str = "*"

    JWT_ACCESS_TOKEN_EXPIRES: int = 3600
    MONGO_READ_ONLY: bool = False

    class Config:
        env_file = ".env"


class DevConfig(BaseConfig):
    MONGO_READ_ONLY = False


class StageConfig(BaseConfig):
    MONGO_READ_ONLY = True
    CORS_ORIGINS = "https://purple-tree-030320a03.2.azurestaticapps.net"
