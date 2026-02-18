from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from datetime import datetime
from app.db import get_db
from app.security import hash_password, verify_password
from app.models import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register(data: RegisterRequest):
    db = get_db()

    if db.users.find_one({"email": data.email}):
        raise HTTPException(400, "User already exists")

    db.users.insert_one({
        "email": data.email,
        "password": hash_password(data.password),
        "created_at": datetime.utcnow(),
    })

    return {"msg": "User created"}


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, Authorize: AuthJWT = Depends()):
    db = get_db()
    user = db.users.find_one({"email": data.email})

    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(401, "Bad credentials")

    token = Authorize.create_access_token(subject=str(user["_id"]))
    return {"access_token": token}
