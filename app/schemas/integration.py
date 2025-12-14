# app/schemas/integration.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from .base import BaseSchema

class IntegrationBase(BaseModel):
    integration_type: str = Field(..., max_length=20)  # native, api, webhook, zapier
    ease_of_setup: Optional[str] = Field(None, max_length=10)  # easy, medium, complex
    documentation_url: Optional[HttpUrl] = None
    is_official: bool = False

class IntegrationCreate(IntegrationBase):
    integrates_with: int  # tool_id of the integrated tool

class IntegrationUpdate(IntegrationBase):
    integration_type: Optional[str] = Field(None, max_length=20)
    integrates_with: Optional[int] = None

class IntegrationInDB(IntegrationBase, BaseSchema):
    tool_id: int
    integrates_with: int

    class Config:
        from_attributes = True

class Integration(IntegrationInDB):
    integrated_tool_name: Optional[str] = None