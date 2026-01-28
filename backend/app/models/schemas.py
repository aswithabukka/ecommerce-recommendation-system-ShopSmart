from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ===== EVENT SCHEMAS =====


class EventCreate(BaseModel):
    """Schema for creating a new event."""
    user_id: str = Field(..., description="External user ID or session ID")
    product_id: int = Field(..., description="Product ID")
    event_type: str = Field(..., pattern="^(view|add_to_cart|purchase)$")
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    """Schema for event response."""
    id: int
    user_id: int
    product_id: int
    event_type: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ===== PRODUCT SCHEMAS =====


class ProductBase(BaseModel):
    """Base product schema."""
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    external_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductWithScore(ProductResponse):
    """Product with recommendation/trending score."""
    score: Optional[float] = None
    rank: Optional[int] = None


class ProductSearchResponse(BaseModel):
    """Schema for product search results."""
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ===== RECOMMENDATION SCHEMAS =====


class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""
    user_id: str
    recommendations: List[ProductWithScore]
    strategy: str = Field(..., description="personalized, trending, or cold_start_category")
    generated_at: datetime


class SimilarProductsResponse(BaseModel):
    """Schema for similar products response."""
    product_id: int
    similar_products: List[ProductWithScore]
    generated_at: datetime


# ===== ADMIN SCHEMAS =====


class DailyEventStatsResponse(BaseModel):
    """Schema for daily event statistics."""
    date: datetime
    event_type: str
    event_count: int
    unique_users: int
    unique_products: int

    class Config:
        from_attributes = True


class TrendingProductResponse(BaseModel):
    """Schema for trending product."""
    product: ProductResponse
    score: float
    event_count: int
    time_window: str


class ApiStatsResponse(BaseModel):
    """Schema for API statistics."""
    endpoint: str
    request_count: int
    avg_response_time_ms: Optional[float]
    error_count: int


class AdminDashboardResponse(BaseModel):
    """Schema for admin dashboard."""
    events_by_day: List[DailyEventStatsResponse]
    top_trending: List[TrendingProductResponse]
    api_stats: Dict[str, Any]
    total_events: int
    total_users: int
    total_products: int


# ===== HEALTH SCHEMAS =====


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    database: str
    redis: str
    timestamp: datetime
