from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from jose import jwt, JWTError
from typing import AsyncGenerator
from app.models.user import User
from sqlalchemy import select
from app.models.refresh_token import RefreshToken

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(token: str, db: AsyncSession = Depends(get_db)) -> User:
    from app.core.security import settings
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check user exists
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check token revocation
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.token == token,
        RefreshToken.revoked == False
    )
    result = await db.execute(stmt)
    token_obj = result.scalar_one_or_none()
    if token_obj is None:
        raise HTTPException(status_code=401, detail="Token revoked or invalid")
    
    return user


def require_role(*roles):
    """
    FastAPI dependency to enforce user roles.
    Usage:
        @router.get("/admin")
        async def admin_route(current_user=Depends(require_role("admin"))):
            ...
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
