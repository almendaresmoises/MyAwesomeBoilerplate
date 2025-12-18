from fastapi import APIRouter, Depends, HTTPException, Body, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tenant import Tenant
from app.api.deps import get_db
from typing import List, Optional

router = APIRouter(prefix="/tenants", tags=["tenants"])

# -------------------------
# REGISTER TENANT
# -------------------------
@router.post("/register")
async def register_tenant(
    name: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Tenant).where(Tenant.name == name)
    result = await db.execute(stmt)
    existing_tenant = result.scalar_one_or_none()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant with name '{name}' already exists"
        )

    tenant = Tenant(name=name)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    return {
        "tenant_id": str(tenant.tenant_id),
        "name": tenant.name,
        "is_active": tenant.is_active,
        "created_at": tenant.created_at
    }

# -------------------------
# LIST TENANTS
# -------------------------
@router.get("/list", response_model=List[dict])
async def list_tenants(
    name: Optional[str] = Query(None, description="Filter tenants by name"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Tenant)
    if name:
        stmt = stmt.where(Tenant.name.ilike(f"%{name}%"))

    result = await db.execute(stmt)
    tenants = result.scalars().all()

    return [
        {
            "tenant_id": str(t.tenant_id),
            "name": t.name,
            "is_active": t.is_active,
            "created_at": t.created_at
        }
        for t in tenants
    ]
