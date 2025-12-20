from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.core.security import hash_password, create_access_token, create_refresh_token, verify_password
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from app.schemas.auth import Login
from app.services.auth_service import AuthService
import uuid

router = APIRouter()

# -------------------------
# LOGIN
# -------------------------
@router.post("/login")
async def login(payload: Login, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        access_token, refresh_token, user = await auth_service.login(payload.email, payload.password)
        return {
            "msg": "Login successful",
            "user_id": str(user.user_id),
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


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
    # ensure UUID format
    tenant_id = uuid.UUID(tenant_id)

    stmt = select(User).where(
        User.email == email,
        User.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = hash_password(password)
    user = User(
        user_id=uuid.uuid4(),
        email=email,
        hashed_password=hashed_pw,
        tenant_id=tenant_id,
        role="user"
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "tenant_id": str(user.tenant_id)
    }



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

    new_refresh = create_refresh_token(str(token_obj.user_id))
    new_access = create_access_token(str(token_obj.user_id))


    new_token_obj = RefreshToken(
        token=new_refresh,
        user_id=token_obj.user_id,
        tenant_id=token_obj.tenant_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_MIN)
    )
    db.add(new_token_obj)
    await db.commit()
    await db.refresh(new_token_obj)

    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}


# -------------------------
# LOGOUT
# -------------------------
@router.post("/logout")
async def logout(refresh_token: str = Body(...), db: AsyncSession = Depends(get_db)):
    stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
    result = await db.execute(stmt)
    token_obj = result.scalar_one_or_none()

    if token_obj:
        # Revoke all refresh tokens of this user within this tenant
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == token_obj.user_id,
            RefreshToken.tenant_id == token_obj.tenant_id
        )
        result = await db.execute(stmt)
        all_tokens = result.scalars().all()
        for t in all_tokens:
            t.revoked = True
        await db.commit()

    return {"detail": "Logged out successfully"}


# -------------------------
# CURRENT USER
# -------------------------
@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.user_id,
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
