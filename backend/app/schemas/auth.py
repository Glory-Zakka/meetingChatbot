from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: str
    user_role: str
    full_name: str


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None