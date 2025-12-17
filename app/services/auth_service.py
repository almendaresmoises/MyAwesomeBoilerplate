from fastapi import HTTPException
from app.repositories.user_repo import UserRepository
from app.core.security import verify_password, hash_password
from app.core.jwt_manager import create_access_token, create_refresh_token

class AuthService:

    @staticmethod
    async def register_user(db, email, password):
        existing = await UserRepository.get_by_email(db, email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = hash_password(password)
        user = await UserRepository.create(db, email, hashed)
        return user

    @staticmethod
    async def authenticate(db, email, password):
        user = await UserRepository.get_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))

        return access, refresh, user
