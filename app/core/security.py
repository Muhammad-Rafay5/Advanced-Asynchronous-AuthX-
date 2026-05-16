from datetime import datetime, timedelta, timezone
from typing import Any, Union
from uuid import uuid4
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.BCRYPT_ROUNDS)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_token(subject: Union[str, Any], expires_delta: timedelta, secret: str, token_type: str) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": token_type,
        "jti": str(uuid4()),
    }
    return jwt.encode(to_encode, secret, algorithm=settings.ALGORITHM)

def create_access_token(subject: Union[str, Any]) -> str:
    return create_token(subject, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), settings.ACCESS_TOKEN_SECRET, "access")

def create_refresh_token(subject: Union[str, Any]) -> str:
    return create_token(subject, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), settings.REFRESH_TOKEN_SECRET, "refresh")

def decode_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=[settings.ALGORITHM])

