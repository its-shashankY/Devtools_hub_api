# app/api/v1/endpoints/tools.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi_pagination import Page, paginate, Params
from pydantic import BaseModel, Field
from app.database.session import get_db
from app.schemas.tool import Tool, ToolInDB, ToolCreate, ToolUpdate, ToolList
from app.services.tool_service import ToolService
from app.core.security import get_current_active_user
from app.schemas.user import User

router = APIRouter()

class ToolCompareRequest(BaseModel):
    tool_ids: List[int] = Field(..., min_length=2, max_length=5, description="List of tool IDs to compare")


@router.get("/", response_model=Page[Tool])
def get_tools(
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    features: Optional[List[str]] = Query(None),
    sort: str = "name",
    params: Params = Depends()
):
    """
    Get paginated list of tools with filtering and sorting options.
    """
    tools = ToolService.get_tools(
        db,
        category=category,
        price_min=price_min,
        price_max=price_max,
        features=features,
        sort=sort
    )
    return paginate(tools, params)

@router.get("/{tool_id}", response_model=ToolInDB)
def get_tool(
    tool_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific tool.
    """
    tool = ToolService.get_tool(db, tool_id=tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    return tool

@router.get("/{tool_id}/alternatives", response_model=List[Tool])
def get_tool_alternatives(
    tool_id: int,
    min_similarity: int = 50,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get alternative tools for a specific tool.
    """
    return ToolService.get_alternatives(
        db, 
        tool_id=tool_id,
        min_similarity=min_similarity,
        limit=limit
    )

@router.get("/{tool_id}/pricing", response_model=dict)
def get_tool_pricing(
    tool_id: int,
    include_history: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get pricing information for a specific tool.
    """
    return ToolService.get_pricing(db, tool_id, include_history)

@router.get("/{tool_id}/reviews", response_model=dict)
def get_tool_reviews(
    tool_id: int,
    db: Session = Depends(get_db)
):
    """
    Get review information for a specific tool.
    """
    return ToolService.get_reviews(db, tool_id)


@router.post("/compare", response_model=dict)
def compare_tools(
    request: ToolCompareRequest,
    db: Session = Depends(get_db)
):
    """
    Compare multiple tools side by side.
    """
    tool_ids = request.tool_ids
    
    if len(tool_ids) < 2 or len(tool_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must compare between 2 and 5 tools"
        )
    
    return ToolService.compare_tools(db, tool_ids)