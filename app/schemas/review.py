# app/schemas/review.py
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from .base import BaseSchema

class ReviewAggregateBase(BaseModel):
    source: str = Field(..., max_length=50)
    avg_rating: float = Field(..., ge=0, le=5)
    total_reviews: int = Field(..., ge=0)
    rating_breakdown: Dict[str, int] = {}
    source_url: Optional[str] = None
    last_scraped_at: Optional[datetime] = None

class ReviewAggregateCreate(ReviewAggregateBase):
    pass

class ReviewAggregateUpdate(ReviewAggregateBase):
    source: Optional[str] = Field(None, max_length=50)
    avg_rating: Optional[float] = Field(None, ge=0, le=5)
    total_reviews: Optional[int] = Field(None, ge=0)

class ReviewAggregateInDB(ReviewAggregateBase, BaseSchema):
    tool_id: int

    class Config:
        from_attributes = True

class ReviewAggregate(ReviewAggregateInDB):
    pass