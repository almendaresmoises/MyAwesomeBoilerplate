from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.core.security import hash_password, create_access_token, create_refresh_token, verify_password
from datetime import datetime, timedelta, UTC
from app.models.refresh_token import RefreshToken
from fastapi import Body
import uuid


router = APIRouter()

@router.post("/login")
async def login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    
    token_obj = RefreshToken(token=refresh, user_id=user.id,
                             expires_at=datetime.now(UTC)+timedelta(days=7))
    db.add(token_obj)
    await db.commit()
    
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


@router.post("/register")
async def register(
    email: str = Body(...),
    password: str = Body(...),
    tenant_id: str = Body(...),
    db: AsyncSession = Depends(get_db)
):
    # Check if user exists in tenant
    stmt = select(User).where(User.email == email, User.tenant_id == tenant_id)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed = hash_password(password)
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed,
        tenant_id=tenant_id,
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "email": user.email, "tenant_id": user.tenant_id}

@router.post("/refresh")
async def refresh_token(refresh_token: str = Body(...), db: AsyncSession = Depends(get_db)):
    stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
    result = await db.execute(stmt)
    token_obj = result.scalar_one_or_none()
    
    if not token_obj or token_obj.revoked or token_obj.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Rotate
    token_obj.revoked = True
    new_refresh = create_refresh_token(token_obj.user_id)
    new_access = create_access_token(token_obj.user_id)
    
    new_token_obj = RefreshToken(
        token=new_refresh,
        user_id=token_obj.user_id,
        expires_at=datetime.now(UTC) + timedelta(days=7)
    )
    db.add(new_token_obj)
    await db.commit()
    
    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}


@router.post("/logout")
async def logout(refresh_token: str = Body(...), db: AsyncSession = Depends(get_db)):
    stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
    result = await db.execute(stmt)
    token_obj = result.scalar_one_or_none()
    
    if token_obj:
        token_obj.revoked = True
        await db.commit()
    
    return {"detail": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
    }

@router.get("/admin/data")
async def admin_data(current_user: User = Depends(require_role("admin"))):
    return {"data": "Sensitive admin-only data"}

