from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.core.config import settings
from app.models.refresh_token import RefreshToken
from app.core.security import hash_password, create_access_token, create_refresh_token, verify_password
from datetime import datetime, timedelta, timezone
import uuid

router = APIRouter()
# -------------------------
# LOGIN
# -------------------------
@router.post("/login")
async def login(email: str = Body(...), password: str = Body(...), db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token(user.id)

    # Save both tokens in DB
    access_token_obj = RefreshToken(
        token=access_token,
        user_id=user.id,
        tenant_id=user.tenant_id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MIN)
    )
    refresh_token_obj = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        tenant_id=user.tenant_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )

    db.add_all([access_token_obj, refresh_token_obj])
    await db.commit()
    await db.refresh(access_token_obj)
    await db.refresh(refresh_token_obj)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer"
    }


# -------------------------
# LOGOUT
# -------------------------
@router.post("/logout")
async def logout(refresh_token: str = Body(...), db: AsyncSession = Depends(get_db)):
    # Get refresh token object
    stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
    result = await db.execute(stmt)
    token_obj = result.scalar_one_or_none()

    if token_obj:
        # Revoke all tokens for this user
        stmt = select(RefreshToken).where(RefreshToken.user_id == token_obj.user_id)
        result = await db.execute(stmt)
        all_tokens = result.scalars().all()
        for t in all_tokens:
            t.revoked = True

        await db.commit()

    return {"detail": "Logged out successfully"}

# -------------------------
# REGISTER
# -------------------------
@router.post("/register")
async def register(
    email: str = Body(...),
    password: str = Body(...),
    tenant_id: str = Body(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == email, User.tenant_id == tenant_id)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    hashed_pw = hash_password(password)
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed_pw,
        tenant_id=tenant_id,
        role="user"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "email": user.email, "tenant_id": user.tenant_id}


# -------------------------
# REFRESH TOKEN
# -------------------------
@router.post("/refresh")
async def refresh_token(refresh_token: str = Body(...), db: AsyncSession = Depends(get_db)):
    stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
    result = await db.execute(stmt)
    token_obj = result.scalar_one_or_none()

    if not token_obj or token_obj.revoked or token_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Revoke old token
    token_obj.revoked = True

    new_refresh = create_refresh_token(token_obj.user_id)
    new_access = create_access_token(token_obj.user_id)

    new_token_obj = RefreshToken(
        token=new_refresh,
        user_id=token_obj.user_id,
        tenant_id=token_obj.tenant_id,  # pass tenant_id
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(new_token_obj)
    await db.commit()
    await db.refresh(new_token_obj)

    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

# -------------------------
# CURRENT USER
# -------------------------
@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id
    }


# -------------------------
# ADMIN-ONLY DATA
# -------------------------
@router.get("/admin/data")
async def admin_data(current_user: User = Depends(require_role("admin"))):
    return {"data": "Sensitive admin-only data"}
