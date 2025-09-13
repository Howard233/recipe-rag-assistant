# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Recipe Assistant"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings (for future use)
    DATABASE_URL: Optional[str] = None
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"

    # OpenAI key
    OPENAI_API_KEY: str
    QDRANT_URL: str
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        extra = "allow"
settings = Settings()