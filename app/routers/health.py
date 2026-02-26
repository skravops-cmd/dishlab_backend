from fastapi import APIRouter
from fastapi import Depends
from app.config import DevConfig, StageConfig
from app.db import get_db
from pymongo.errors import PyMongoError
import os

router = APIRouter(prefix="/health", tags=["health"])

_env = os.getenv("FLASK_ENV", "development")
settings = StageConfig() if _env == "staging" else DevConfig()


@router.get("")
def health():
    """
    Liveness probe — API is running
    """
    return {
        "status": "ok",
        "service": "dishlab-api",
        "environment": _env,
    }


@router.get("/ready")
def readiness(db=Depends(get_db)):
    """
    Readiness probe — dependencies are reachable
    """
    try:
        db.client.admin.command("ping")
    except PyMongoError as e:
        return {
            "status": "error",
            "dependency": "mongo",
            "detail": str(e),
        }

    return {
        "status": "ready",
        "mongo": "ok",
        "read_only": settings.MONGO_READ_ONLY,
    }
