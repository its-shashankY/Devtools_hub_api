# app/schemas/tool.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from .base import BaseSchema
from .pricing import PricingTier
from .review import ReviewAggregate
from .feature import Feature

class ToolBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    description: Optional[str] = None
    tagline: Optional[str] = Field(None, max_length=500)
    website_url: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    founded_date: Optional[date] = None
    company_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = True

class ToolCreate(ToolBase):
    category_id: Optional[int] = None

class ToolUpdate(ToolBase):
    name: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=255, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    category_id: Optional[int] = None

class ToolInDB(ToolBase, BaseSchema):
    category_id: Optional[int] = None
    query_count: int = 0
    last_queried_at: Optional[datetime] = None

class Tool(ToolBase):
    id: int
    category_name: Optional[str] = None
    avg_price: Optional[float] = None
    avg_rating: Optional[float] = None

class ToolDetail(ToolInDB):
    pricing_tiers: List[PricingTier] = []
    reviews: Optional[ReviewAggregate] = None
    features: List[Feature] = []
    integration_count: int = 0

class ToolList(BaseModel):
    items: List[Tool]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True

class ToolComparison(BaseModel):
    tools: Dict[int, Tool]
    common_features: List[str]
    unique_features: Dict[int, List[str]]
    pricing: Dict[int, Dict[str, Any]]
    reviews: Dict[int, Dict[str, Any]]
    integration_counts: Dict[int, int]