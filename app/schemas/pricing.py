# app/schemas/pricing.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from .base import BaseSchema

class PricingTierBase(BaseModel):
    tier_name: str = Field(..., max_length=100)
    monthly_price: Optional[float] = None
    annual_price: Optional[float] = None
    currency: str = "USD"
    billing_cycle: Optional[str] = None  # monthly, annual, one-time
    features_json: Dict[str, Any] = {}
    limits_json: Dict[str, Any] = {}
    is_current: bool = True
    effective_from: datetime

class PricingTierCreate(PricingTierBase):
    pass

class PricingTierUpdate(PricingTierBase):
    tier_name: Optional[str] = Field(None, max_length=100)
    effective_from: Optional[datetime] = None

class PricingTierInDB(PricingTierBase, BaseSchema):
    tool_id: int

    class Config:
        from_attributes = True

class PricingTier(PricingTierInDB):
    pass