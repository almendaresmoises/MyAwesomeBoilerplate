from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.deps import get_db, require_role
from app.models.user import User
from app.core.security import hash_password

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# -----------------------------
# Get all users for tenant
# -----------------------------
@router.get("/", response_model=List[dict])
async def list_users(
    current_user: User = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [{"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active} for u in users]

# -----------------------------
# Get specific user by ID
# -----------------------------
@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == user_id, User.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}

# -----------------------------
# Update user role or status
# -----------------------------
@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    role: str = Body(None),
    is_active: bool = Body(None),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == user_id, User.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if role:
        user.role = role
    if is_active is not None:
        user.is_active = is_active

    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}

# -----------------------------
# Reset user password
# -----------------------------
@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    new_password: str = Body(...),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == user_id, User.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(new_password)
    await db.commit()
    return {"detail": "Password reset successfully"}

# -----------------------------
# Delete user
# -----------------------------
@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == user_id, User.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"detail": "User deleted successfully"}
