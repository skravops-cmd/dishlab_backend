from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(RegisterRequest):
    pass


class TokenResponse(BaseModel):
    access_token: str


class ReceiptCreate(BaseModel):
    name: str
    cuisine: str
    ingredients: str
    youtube_link: HttpUrl


class ReceiptUpdate(BaseModel):
    name: Optional[str]
    cuisine: Optional[str]
    ingredients: Optional[str]
    youtube_link: Optional[HttpUrl]


class ReceiptOut(BaseModel):
    id: str
    name: str
    cuisine: str
    ingredients: List[str]
    youtube_link: str
