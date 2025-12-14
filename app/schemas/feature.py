# app/schemas/feature.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .base import BaseSchema

class FeatureBase(BaseModel):
    feature_name: str = Field(..., max_length=255)
    feature_category: Optional[str] = Field(None, max_length=100)
    is_available: bool = True
    tier_availability: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None

class FeatureCreate(FeatureBase):
    tool_id: int

class FeatureUpdate(FeatureBase):
    feature_name: Optional[str] = Field(None, max_length=255)
    feature_category: Optional[str] = Field(None, max_length=100)
    is_available: Optional[bool] = None
    tier_availability: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None

class FeatureInDB(FeatureBase, BaseSchema):
    tool_id: int

    class Config:
        from_attributes = True

class Feature(FeatureInDB):
    pass