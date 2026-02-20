from fastapi import APIRouter
from app.db import client
from app.config import DevConfig, StageConfig
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
def readiness():
    """
    Readiness probe — dependencies are reachable
    """
    try:
        # MongoDB ping
        client.admin.command("ping")
    except Exception as e:
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