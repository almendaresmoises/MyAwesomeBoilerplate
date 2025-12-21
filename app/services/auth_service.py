from fastapi import HTTPException
from app.repositories.user_repo import UserRepository
from app.repositories.token_repo import TokenRepository
from app.core.security import verify_password, hash_password, hash_token
from app.core.jwt_manager import create_access_token, create_refresh_token
from app.models.refresh_token import RefreshToken
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

class AuthService:

    @staticmethod
    async def register_user(db: AsyncSession, email: str, password: str):
        existing = await UserRepository.get_by_email(db, email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = hash_password(password)
        user = await UserRepository.create(db, email, hashed)
        return user
            # Print for debugging

    @staticmethod
    async def store_refresh_token(
        db: AsyncSession,
        user_id: UUID,
        refresh_hash: str
    ):
        new_token = await TokenRepository.save_refresh_token(
            db,
            user_id=user_id,
            token_hash=refresh_hash
        )

        await db.commit()
        await db.refresh(new_token)  # optional

        return new_token

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str):
        # 1. Fetch user
        user = await UserRepository.get_by_email(db, email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # 2. Verify password
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # 3. Issue tokens
        access_token = create_access_token(str(user.user_id))
        refresh_token = create_refresh_token(str(user.user_id))
        hashed_refresh_token = hash_token(refresh_token)

        # 4. Persist hashed refresh token
        refresh_token_obj = await TokenRepository.save_refresh_token(
            db=db,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            token_hash=hashed_refresh_token,
        )

        # 5. Commit transaction
        try:
            await db.commit()
            await db.refresh(refresh_token_obj)
        except Exception:
            await db.rollback()
            raise

        return access_token, refresh_token, user

