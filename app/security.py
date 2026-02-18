from pydantic import BaseSettings
from fastapi_jwt_auth import AuthJWT
from passlib.context import CryptContext
from app.config import DevConfig, StageConfig
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_env = os.getenv("FLASK_ENV", "development")
settings = StageConfig() if _env == "staging" else DevConfig()


class JWTSettings(BaseSettings):
    authjwt_secret_key: str = settings.JWT_SECRET_KEY


@AuthJWT.load_config
def get_config():
    return JWTSettings()


def hash_password(password: str) -> str:
    # Truncate to 72 bytes to satisfy bcrypt
    return pwd_context.hash(password.encode('utf-8')[:72])


def verify_password(plain, hashed) -> bool:
    return pwd_context.verify(plain, hashed)
0
