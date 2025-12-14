# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import tools, categories, search, analytics

api_router = APIRouter()

api_router.include_router(tools.router, prefix="/tools", tags=["Tools"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])