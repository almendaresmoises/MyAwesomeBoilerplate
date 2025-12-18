import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="users")
    refresh_tokens = relationship("RefreshToken", cascade="all, delete-orphan", back_populates="user")
