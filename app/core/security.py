# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.config import settings
from app.database.session import get_db
from app.models.user import User
from app.models.api_key import APIKey

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for API key authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get the current user from the API key."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # For API key authentication, the token is the API key itself
        api_key = token
        
        # Look up the API key in the database
        api_key_record = db.query(APIKey).filter(
            APIKey.api_key == api_key,
            APIKey.is_active == True,
            (APIKey.expires_at.is_(None) | (APIKey.expires_at > datetime.utcnow()))
        ).first()
        
        if not api_key_record:
            raise credentials_exception
            
        # Get the associated user
        user = db.query(User).filter(User.id == api_key_record.user_id).first()
        if not user:
            raise credentials_exception
            
        return user
        
    except Exception as e:
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_user_permissions(user: User, required_tier: str) -> bool:
    """Check if user has the required tier for an action."""
    tier_order = {"free": 0, "paid": 1}
    return tier_order.get(user.tier.value, 0) >= tier_order.get(required_tier, 0)