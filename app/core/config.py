# app/core/config.py
from pydantic import validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
from functools import lru_cache
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "DevTools Hub API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "DEVELOPMENT"
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL","postgresql://devtools_hub_user:yP5kU38F7m0fcQwV5g0HKd7CD0bF8KQu@dpg-d4vd0ppr0fns739j0qog-a/devtools_hub")
    
    # CORS - Using Any type and more flexible parsing
    BACKEND_CORS_ORIGINS: Any = ["*"]
    
    @validator('BACKEND_CORS_ORIGINS', pre=True)
    def assemble_cors_origins(cls, v):
        if v is None:
            return ["*"]
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            if v.startswith('[') and v.endswith(']'):
                # Handle JSON array string
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Handle comma-separated string
            return [i.strip('"\' ') for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]  # Default fallback
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Rate Limiting
    RATE_LIMIT_PER_HOUR: int = 1000
    ANONYMOUS_RATE_LIMIT: int = 100
    
    # API Key Settings
    API_KEY_PREFIX: str = "xano_sk_"
    API_KEY_LENGTH: int = 40
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Create settings instance
settings = get_settings()