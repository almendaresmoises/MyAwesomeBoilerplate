from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

#password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

#refresh token
def hash_token(token: str) -> str:
    return pwd_context.hash(token)

def verify_hashed_token(raw: str, hashed: str) -> bool:
    return pwd_context.verify(raw, hashed)

def create_refresh_token(sub: str):
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_MIN)
    return jwt.encode({"sub": sub, "exp": expire}, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

#jwt
def create_access_token(sub: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MIN)
    return jwt.encode({"sub": sub, "exp": expire}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
