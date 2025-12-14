# app/schemas/base.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class BaseSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int