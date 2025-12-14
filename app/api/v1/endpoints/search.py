# app/api/v1/endpoints/search.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.search_service import SearchService
from app.schemas.tool import ToolList

router = APIRouter()

@router.get("/tools", response_model=Dict[str, Any])
async def search_tools(
    q: str = Query(..., min_length=1, description="Search query string"),
    category: Optional[str] = None,
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    price_max: Optional[float] = Query(None, gt=0, description="Maximum price filter"),
    features: Optional[List[str]] = Query(None, description="List of required features"),
    sort_by: str = "relevance",
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search for tools with various filters and sorting options.
    """
    try:
        # Calculate pagination
        offset = (page - 1) * size
        
        # Perform search
        results = SearchService.search_tools(
            db=db,
            query=q,
            category=category,
            price_min=price_min,
            price_max=price_max,
            features=features
        )
        
        # Apply sorting
        if sort_by == "price_asc":
            results = results.order_by(PricingTier.monthly_price.asc())
        elif sort_by == "price_desc":
            results = results.order_by(PricingTier.monthly_price.desc())
        elif sort_by == "rating":
            results = results.outerjoin(ReviewAggregate).order_by(
                desc(ReviewAggregate.avg_rating)
            )
        elif sort_by == "recent":
            results = results.order_by(desc(Tool.created_at))
        
        # Apply pagination
        total = results.count()
        items = results.offset(offset).limit(size).all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while searching: {str(e)}"
        )

@router.get("/suggestions", response_model=List[str])
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="Partial search query"),
    limit: int = Query(5, ge=1, le=10, description="Number of suggestions to return"),
    db: Session = Depends(get_db)
) -> List[str]:
    """
    Get search suggestions based on partial input.
    """
    try:
        return SearchService.get_search_suggestions(db=db, query=q, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching suggestions: {str(e)}"
        )

@router.get("/filters", response_model=Dict[str, Any])
async def get_search_filters(
    q: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get available search filters and their values.
    """
    try:
        return SearchService.get_available_filters(db=db, query=q)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching filters: {str(e)}"
        )
