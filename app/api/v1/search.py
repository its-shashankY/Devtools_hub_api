# app/api/v1/endpoints/search.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi_pagination import Page, paginate

from app.database.session import get_db
from app.schemas.tool import Tool
from app.services.search_service import SearchService

router = APIRouter()

@router.get("/", response_model=Page[Tool])
def search_tools(
    q: str = Query(..., min_length=3, max_length=100),
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    features: Optional[List[str]] = Query(None),
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Full-text search across tools.
    """
    results = SearchService.search_tools(
        db,
        query=q,
        category=category,
        price_min=price_min,
        price_max=price_max,
        features=features
    )
    return paginate(results)

@router.get("/trending", response_model=List[dict])
def get_trending_tools(
    period: str = "7d",
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get trending tools based on query count and rating.
    """
    valid_periods = ["24h", "7d", "30d"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
        )
    
    return SearchService.get_trending_tools(db, period=period, limit=limit)

@router.get("/recently-updated", response_model=List[dict])
def get_recently_updated(
    change_type: Optional[str] = None,
    days: int = 30,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get recently updated tools.
    """
    valid_change_types = ["pricing", "feature", "update"]
    if change_type and change_type not in valid_change_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid change_type. Must be one of: {', '.join(valid_change_types)}"
        )
    
    return SearchService.get_recently_updated(
        db,
        change_type=change_type,
        days=days,
        limit=limit
    )

@router.get("/recommendations/{tool_id}", response_model=List[dict])
def get_recommendations(
    tool_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get tool recommendations based on similarity.
    """
    return SearchService.get_recommendations(
        db,
        tool_id=tool_id,
        limit=limit
    )