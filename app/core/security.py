from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(sub: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MIN)
    return jwt.encode({"sub": sub, "exp": expire}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(sub: str):
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_MIN)
    return jwt.encode({"sub": sub, "exp": expire}, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
