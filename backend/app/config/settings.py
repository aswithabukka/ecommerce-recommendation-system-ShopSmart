from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://shopsmart:shopsmart_secret@localhost:5432/shopsmart"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    cors_origins: Union[List[str], str] = "http://localhost:3000,http://localhost:5173,http://localhost:80"

    # App settings
    debug: bool = True
    app_name: str = "ShopSmart API"
    app_version: str = "1.0.0"

    # Cache TTLs (in seconds)
    cache_ttl_recommendations: int = 300  # 5 minutes
    cache_ttl_similar_products: int = 3600  # 1 hour
    cache_ttl_trending: int = 900  # 15 minutes
    cache_ttl_admin: int = 60  # 1 minute

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(',')]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


settings = Settings()
