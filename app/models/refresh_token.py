from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, func
from app.db.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_token"
    token = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
