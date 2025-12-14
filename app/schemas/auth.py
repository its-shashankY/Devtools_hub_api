# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class UserTier(str, Enum):
    FREE = "free"
    PAID = "paid"

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        # Add more password strength validations as needed
        return v

class UserInDB(UserBase):
    id: int
    tier: UserTier
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    api_key: str

class APIKeyCreate(BaseModel):
    key_name: str
    tier: UserTier = UserTier.FREE

class APIKeyInDB(BaseModel):
    id: int
    key_name: str
    tier: UserTier
    rate_limit: int
    requests_today: int
    requests_this_hour: int
    last_request_at: Optional[datetime] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UsageStats(BaseModel):
    requests_today: int
    requests_this_hour: int
    rate_limit: int
    remaining: int
    resets_at: datetime