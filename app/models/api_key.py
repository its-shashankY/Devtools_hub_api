# app/models/api_key.py
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.base_class import Base
from app.models.user import UserTier
import secrets

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    api_key = Column(String(64), unique=True, index=True, nullable=False)
    key_name = Column(String(255))
    tier = Column(Enum(UserTier), default=UserTier.FREE, nullable=False)
    rate_limit = Column(Integer, default=100)
    requests_today = Column(Integer, default=0)
    requests_this_hour = Column(Integer, default=0)
    last_request_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="api_keys")

    @staticmethod
    def generate_key() -> str:
        return "xano_sk_" + secrets.token_urlsafe(32)