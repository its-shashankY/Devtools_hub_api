# app/api/v1/endpoints/auth.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any

from app.core.security import (
    get_password_hash,
    create_access_token,
    verify_password
)
from app.core.config import settings
from app.database.session import get_db
from app.models.user import User, UserTier
from app.models.api_key import APIKey
from app.schemas.auth import (
    UserCreate,
    UserInDB,
    Token,
    APIKeyCreate,
    APIKeyInDB,
    UsageStats
)

router = APIRouter()

@router.post("/register", response_model=dict)
async def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=user_in.email,
        name=user_in.name,
        password_hash=get_password_hash(user_in.password),
        tier=UserTier.FREE
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate API key for the user
    api_key = APIKey(
        user_id=user.id,
        api_key=APIKey.generate_key(),
        key_name="Default Key",
        tier=UserTier.FREE,
        rate_limit=100
    )
    db.add(api_key)
    db.commit()
    
    return {
        "success": True,
        "data": {
            "user_id": user.id,
            "api_key": api_key.api_key,
            "tier": user.tier.value
        }
    }

@router.post("/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get or create API key
    api_key = db.query(APIKey).filter(
        APIKey.user_id == user.id,
        APIKey.is_active == True
    ).first()
    
    if not api_key:
        api_key = APIKey(
            user_id=user.id,
            api_key=APIKey.generate_key(),
            key_name="Login Key",
            tier=user.tier,
            rate_limit=100 if user.tier == UserTier.FREE else 5000
        )
        db.add(api_key)
        db.commit()
    
    return {
        "success": True,
        "data": {
            "api_key": api_key.api_key,
            "tier": user.tier.value
        }
    }

@router.get("/usage", response_model=dict)
async def get_usage_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
    api_key_record = db.query(APIKey).filter(APIKey.api_key == api_key).first()
    if not api_key_record or not api_key_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Calculate when the rate limit resets (top of the next hour)
    now = datetime.utcnow()
    next_hour = (now.replace(minute=0, second=0, microsecond=0) + 
                timedelta(hours=1))
    
    return {
        "success": True,
        "data": {
            "requests_today": api_key_record.requests_today,
            "requests_this_hour": api_key_record.requests_this_hour,
            "rate_limit": api_key_record.rate_limit,
            "remaining": max(0, api_key_record.rate_limit - api_key_record.requests_this_hour),
            "resets_at": next_hour.isoformat() + "Z"
        }
    }