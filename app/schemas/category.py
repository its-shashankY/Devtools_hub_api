# app/schemas/category.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from .base import BaseSchema

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=100)
    display_order: int = 0

class CategoryCreate(CategoryBase):
    parent_id: Optional[int] = None

class CategoryUpdate(CategoryBase):
    name: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=255, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    parent_id: Optional[int] = None

class CategoryInDB(CategoryBase, BaseSchema):
    parent_id: Optional[int] = None
    children: List['CategoryInDB'] = []

    class Config:
        from_attributes = True

class Category(CategoryBase):
    id: int
    parent_id: Optional[int] = None
    tool_count: Optional[int] = None

    class Config:
        from_attributes = True

# Update forward refs for recursive models
CategoryInDB.update_forward_refs()