# backend/auth.py

from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import jwt
from pydantic import BaseModel

# ------------ PASSWORD HASHING ------------

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def get_password_hash(password: str) -> str:
    """Hash password using PBKDF2-SHA256."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using PBKDF2."""
    return pwd_context.verify(plain_password, hashed_password)


# ------------ JWT CONFIG ------------

SECRET_KEY = "super-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class TokenData(BaseModel):
    email: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token for login sessions."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
