# app/models/user.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base_class import Base
import enum

class UserTier(str, enum.Enum):
    FREE = "free"
    PAID = "paid"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    tier = Column(Enum(UserTier), default=UserTier.FREE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")