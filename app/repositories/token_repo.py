from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update
from datetime import datetime, timezone, timedelta
from app.core.security import settings
from app.models.refresh_token import RefreshToken

class TokenRepository:

    @staticmethod
    async def save_refresh_token(db: AsyncSession, user_id, tenant_id, token_hash: str):
        obj = RefreshToken(
            token=token_hash,
            user_id=user_id,
            tenant_id=tenant_id,
            expires_at=datetime.now(timezone.utc) + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MIN
            ),
        )
        db.add(obj)
        return obj

    @staticmethod
    async def get_valid_token(db: AsyncSession, user_id, token_hash):
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(None)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_all(db: AsyncSession, user_id):
        stmt = update(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(None)
        ).values(revoked=datetime.utcnow())
        await db.execute(stmt)
        await db.commit()
