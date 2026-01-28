from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.database import TrendingScore, Product
from app.models.schemas import ProductWithScore


class TrendingService:
    """Service for trending product recommendations."""

    def __init__(self, db: Session):
        self.db = db

    def get_global_trending(
        self,
        k: int = 10,
        time_window: str = "7d",
    ) -> List[ProductWithScore]:
        """Get globally trending products."""
        trending = (
            self.db.query(TrendingScore, Product)
            .join(Product, TrendingScore.product_id == Product.id)
            .filter(TrendingScore.time_window == time_window)
            .filter(Product.is_active == True)
            .order_by(desc(TrendingScore.score))
            .limit(k)
            .all()
        )

        return [
            ProductWithScore(
                id=product.id,
                external_id=product.external_id,
                name=product.name,
                description=product.description,
                price=float(product.price) if product.price else None,
                image_url=product.image_url,
                category_id=product.category_id,
                is_active=product.is_active,
                created_at=product.created_at,
                score=score.score,
                rank=idx + 1,
            )
            for idx, (score, product) in enumerate(trending)
        ]

    def get_trending_by_category(
        self,
        category_id: int,
        k: int = 10,
        time_window: str = "7d",
    ) -> List[ProductWithScore]:
        """Get trending products within a specific category."""
        trending = (
            self.db.query(TrendingScore, Product)
            .join(Product, TrendingScore.product_id == Product.id)
            .filter(TrendingScore.time_window == time_window)
            .filter(TrendingScore.category_id == category_id)
            .filter(Product.is_active == True)
            .order_by(desc(TrendingScore.score))
            .limit(k)
            .all()
        )

        return [
            ProductWithScore(
                id=product.id,
                external_id=product.external_id,
                name=product.name,
                description=product.description,
                price=float(product.price) if product.price else None,
                image_url=product.image_url,
                category_id=product.category_id,
                is_active=product.is_active,
                created_at=product.created_at,
                score=score.score,
                rank=idx + 1,
            )
            for idx, (score, product) in enumerate(trending)
        ]

    def get_trending_products_raw(
        self,
        k: int = 10,
        time_window: str = "7d",
    ) -> List[dict]:
        """Get trending products as raw dictionaries (for admin dashboard)."""
        trending = (
            self.db.query(TrendingScore, Product)
            .join(Product, TrendingScore.product_id == Product.id)
            .filter(TrendingScore.time_window == time_window)
            .filter(Product.is_active == True)
            .order_by(desc(TrendingScore.score))
            .limit(k)
            .all()
        )

        return [
            {
                "product": {
                    "id": product.id,
                    "external_id": product.external_id,
                    "name": product.name,
                    "description": product.description,
                    "price": float(product.price) if product.price else None,
                    "image_url": product.image_url,
                    "category_id": product.category_id,
                    "is_active": product.is_active,
                    "created_at": product.created_at.isoformat() if product.created_at else None,
                },
                "score": score.score,
                "event_count": score.event_count,
                "time_window": score.time_window,
            }
            for score, product in trending
        ]
