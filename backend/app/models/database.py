from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    CheckConstraint,
    Date,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Category(Base):
    """Product category model."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")


class Product(Base):
    """Product model."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, nullable=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    image_url = Column(String(1000), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    average_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="products")
    events = relationship("Event", back_populates="product")
    reviews = relationship("ProductReview", back_populates="product")


class ProductReview(Base):
    """Product review and rating model."""
    __tablename__ = "product_reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5"),
    )

    # Relationships
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class User(Base):
    """User model (can be anonymous or registered)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    is_anonymous = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    events = relationship("Event", back_populates="user")
    reviews = relationship("ProductReview", back_populates="user")


class Event(Base):
    """User interaction event model."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    session_id = Column(String(255), nullable=True)
    event_metadata = Column("metadata", JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint("event_type IN ('view', 'add_to_cart', 'purchase')"),
    )

    # Relationships
    user = relationship("User", back_populates="events")
    product = relationship("Product", back_populates="events")


class TrendingScore(Base):
    """Trending scores computed by ML pipeline."""
    __tablename__ = "trending_scores"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    time_window = Column(String(20), nullable=False)
    score = Column(Float, nullable=False)
    event_count = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("time_window IN ('7d', '30d')"),
    )


class ItemSimilarity(Base):
    """Item-to-item similarity scores computed by ML pipeline."""
    __tablename__ = "item_similarity"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    similar_product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    co_occurrence_count = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)


class DailyEventStats(Base):
    """Aggregated daily event statistics for admin dashboard."""
    __tablename__ = "daily_event_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    event_type = Column(String(50), nullable=False)
    event_count = Column(Integer, nullable=False)
    unique_users = Column(Integer, nullable=False)
    unique_products = Column(Integer, nullable=False)


class ApiStats(Base):
    """API request statistics."""
    __tablename__ = "api_stats"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    request_count = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, nullable=True)
    error_count = Column(Integer, default=0)
