import os

# -------------------------------------------------
# Fake env vars for tests (BEFORE app import)
# -------------------------------------------------
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("AUTHJWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/testdb")
os.environ.setdefault("FLASK_ENV", "development")

import pytest
import mongomock
from fastapi.testclient import TestClient

from app.main import app
from app.db import get_db
from app.security import hash_password

# -------------------------
# Fake MongoDB
# -------------------------
@pytest.fixture(scope="function")
def mongo_db():
    client = mongomock.MongoClient()
    return client.dishlab


@pytest.fixture(scope="function")
def client(mongo_db):
    # Override DB dependency
    def override_get_db():
        return mongo_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# -------------------------
# JWT helper
# -------------------------
@pytest.fixture
def auth_headers(client, mongo_db):
    # create user directly
    mongo_db.users.insert_one({
        "email": "user@test.com",
        "password": hash_password("password123")
    })

    res = client.post(
        "/api/auth/login",
        json={"email": "user@test.com", "password": "password123"}
    )

    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
