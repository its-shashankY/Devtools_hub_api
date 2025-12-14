# app/api/v1/endpoints/analytics.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/pricing-trends")
def get_pricing_trends(
    category: Optional[str] = None,
    period: str = "12m",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get pricing trends over time.
    """
    valid_periods = ["3m", "6m", "12m"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
        )
    
    return AnalyticsService.get_pricing_trends(
        db,
        category=category,
        period=period
    )

@router.get("/category-stats")
def get_category_stats(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get statistics by category.
    """
    return AnalyticsService.get_category_stats(db)

@router.get("/tool-stats/{tool_id}")
def get_tool_stats(
    tool_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed statistics for a specific tool.
    """
    stats = AnalyticsService.get_tool_stats(db, tool_id=tool_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    return stats

@router.get("/integration-graph")
def get_integration_graph(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get integration graph data.
    """
    return AnalyticsService.get_integration_graph(db)