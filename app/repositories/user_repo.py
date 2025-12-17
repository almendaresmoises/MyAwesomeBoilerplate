from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

class UserRepository:

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str):
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, email: str, hashed_password: str):
        user = User(email=email, hashed_password=hashed_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def get_by_id(db, id:int):
        stmt = select(User).where(User.id==id)
        return (await db.execute(stmt)).scalar_one_or_none()
