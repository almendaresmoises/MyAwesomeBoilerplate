import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, unique=True)
    name = Column(String, nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
