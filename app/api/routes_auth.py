from fastapi import APIRouter, Depends
from app.schemas.auth import Login, Token
from app.schemas.user import UserCreate, UserOut
from app.services.auth_service import AuthService
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
async def register(payload: UserCreate, db=Depends(get_db)):
    user = await AuthService.register_user(db, payload.email, payload.password)
    return user

@router.post("/login", response_model=Token)
async def login(payload: Login, db=Depends(get_db)):
    access, refresh, user = await AuthService.authenticate(db, payload.email, payload.password)
    return Token(access_token=access, refresh_token=refresh)
