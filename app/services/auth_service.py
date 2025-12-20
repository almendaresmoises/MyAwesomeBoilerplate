from fastapi import HTTPException
from app.repositories.user_repo import UserRepository
from app.core.security import verify_password, hash_password
from app.core.jwt_manager import create_access_token, create_refresh_token
from app.models.refresh_token import RefreshToken
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, email: str, password: str):
        existing = await UserRepository.get_by_email(self.db, email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = hash_password(password)
        user = await UserRepository.create(self.db, email, hashed)
        return user
            # Print for debugging



    async def login(self, email: str, password: str):
        repo = UserRepository(self.db)
        user = await repo.get_by_email(email)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")


        access_token = create_access_token(str(user.user_id))
        refresh_token_str = create_refresh_token(str(user.user_id))

        refresh_token_obj = RefreshToken(
            token=refresh_token_str,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MIN)
        )
        try:
            self.db.add(refresh_token_obj)
            await self.db.commit()
            await self.db.refresh(refresh_token_obj)
        except Exception:
            await self.db.rollback()
            raise

        return access_token, refresh_token_str, user
