from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from jose import jwt, JWTError
from typing import AsyncGenerator
from app.models.user import User
from sqlalchemy import select
from app.models.refresh_token import RefreshToken
from datetime import datetime, timezone

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(token: str, db: AsyncSession = Depends(get_db)) -> User:
    """
    Validate access token and ensure user exists.
    Access tokens are stateless, so we only verify JWT signature and expiration.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Verify user exists
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user  # No DB check for access token revocation — handled by refresh token lifecycle

def require_role(*roles):
    """
    FastAPI dependency to enforce user roles.
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
