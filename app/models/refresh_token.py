import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    refresh_token_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    token = Column(String, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
