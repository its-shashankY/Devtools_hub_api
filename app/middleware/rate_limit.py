# app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.api_key import APIKey
from app.core.config import settings
import time

async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for certain paths
    if request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
        return await call_next(request)
    
    db = SessionLocal()
    try:
        # Get API key from header
        api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not api_key:
            # For anonymous users, use a default rate limit
            response = await call_next(request)
            return response
        
        # Get API key record
        api_key_record = db.query(APIKey).filter(
            APIKey.api_key == api_key,
            APIKey.is_active == True,
            (APIKey.expires_at.is_(None) | (APIKey.expires_at > datetime.utcnow()))
        ).first()
        
        if not api_key_record:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"}
            )
        
        # Check rate limits
        now = datetime.utcnow()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        # Reset hourly counter if needed
        if api_key_record.last_request_at and api_key_record.last_request_at < current_hour:
            api_key_record.requests_this_hour = 0
        
        # Check hourly limit
        if api_key_record.requests_this_hour >= api_key_record.rate_limit:
            reset_time = (current_hour + timedelta(hours=1)).timestamp()
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(int(reset_time - now.timestamp()))},
                content={
                    "detail": f"Rate limit exceeded: {api_key_record.rate_limit} requests per hour",
                    "retry_after": int(reset_time - now.timestamp())
                }
            )
        
        # Process the request
        start_time = time.time()
        response = await call_next(request)
        process_time = int((time.time() - start_time) * 1000)
        
        # Update counters
        api_key_record.requests_this_hour += 1
        api_key_record.requests_today += 1
        api_key_record.last_request_at = now
        db.commit()
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(api_key_record.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(
            api_key_record.rate_limit - api_key_record.requests_this_hour
        )
        response.headers["X-RateLimit-Reset"] = str(int((current_hour + timedelta(hours=1)).timestamp()))
        
        return response
    
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()