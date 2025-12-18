from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings

def create_access_token(sub: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MIN)
    return jwt.encode({"sub": sub, "exp": expire}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(sub: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MIN)
    return jwt.encode({"sub": sub, "exp": expire}, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
