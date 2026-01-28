from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from collections import defaultdict

from app.models.database import Event, User, Product
from app.models.schemas import ProductWithScore
from app.services.trending_service import TrendingService
from app.services.similarity_service import SimilarityService
from app.core.redis import cache_service
from app.config import settings


class RecommendationService:
    """Service for generating personalized recommendations."""

    # Event weights for recommendation scoring
    EVENT_WEIGHTS = {
        "view": 1.0,
        "add_to_cart": 3.0,
        "purchase": 5.0,
    }

    def __init__(self, db: Session):
        self.db = db
        self.trending_service = TrendingService(db)
        self.similarity_service = SimilarityService(db)

    def get_recommendations(
        self,
        user_id: str,
        k: int = 10,
        category_id: Optional[int] = None,
    ) -> Tuple[List[ProductWithScore], str]:
        """
        Get recommendations using strategy selection:
        1. User has history -> collaborative filtering (personalized)
        2. Cold start with category -> trending by category
        3. Cold start without category -> global trending
        """
        # Check cache first
        cache_key = f"rec:{user_id}:{k}:{category_id or 'all'}"
        cached = cache_service.get(cache_key)
        if cached:
            return (
                [ProductWithScore(**p) for p in cached["recommendations"]],
                cached["strategy"],
            )

        # Check if user exists and has history
        user = self.db.query(User).filter(User.external_id == user_id).first()

        if user:
            event_count = self.db.query(Event).filter(Event.user_id == user.id).count()

            if event_count > 0:
                # User has interaction history - use collaborative filtering
                recommendations = self._get_collaborative_recommendations(
                    user.id, k, category_id
                )
                if len(recommendations) >= k // 2:
                    # Cache and return
                    self._cache_recommendations(
                        cache_key, recommendations, "personalized"
                    )
                    return recommendations, "personalized"

        # Cold start fallback
        if category_id:
            # Cold start with category - trending by category
            recommendations = self.trending_service.get_trending_by_category(
                category_id=category_id, k=k, time_window="7d"
            )
            self._cache_recommendations(
                cache_key, recommendations, "cold_start_category"
            )
            return recommendations, "cold_start_category"

        # Global trending
        recommendations = self.trending_service.get_global_trending(k=k, time_window="7d")
        self._cache_recommendations(cache_key, recommendations, "trending")
        return recommendations, "trending"

    def _get_collaborative_recommendations(
        self,
        user_id: int,
        k: int,
        category_id: Optional[int] = None,
    ) -> List[ProductWithScore]:
        """
        Item-to-item collaborative filtering:
        1. Get user's recently interacted products
        2. Find similar products using co-occurrence
        3. Aggregate and rank by similarity score
        4. Filter out already interacted products
        """
        # Get user's recent interactions (last 50)
        recent_events = (
            self.db.query(Event)
            .filter(Event.user_id == user_id)
            .order_by(Event.timestamp.desc())
            .limit(50)
            .all()
        )

        if not recent_events:
            return []

        interacted_product_ids = {e.product_id for e in recent_events}

        # Get similar products for each interacted product
        candidate_scores = defaultdict(lambda: {"score": 0.0, "product": None})

        for event in recent_events:
            # Weight by event type
            weight = self.EVENT_WEIGHTS.get(event.event_type, 1.0)

            similar = self.similarity_service.get_similar_products(
                product_id=event.product_id, k=20
            )

            for product in similar:
                if product.id not in interacted_product_ids:
                    # Apply category filter if specified
                    if category_id and product.category_id != category_id:
                        continue

                    candidate_scores[product.id]["score"] += (product.score or 0) * weight
                    if candidate_scores[product.id]["product"] is None:
                        candidate_scores[product.id]["product"] = product

        # Sort by aggregated score and return top k
        sorted_candidates = sorted(
            candidate_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True,
        )[:k]

        return [
            ProductWithScore(
                id=item["product"].id,
                external_id=item["product"].external_id,
                name=item["product"].name,
                description=item["product"].description,
                price=item["product"].price,
                image_url=item["product"].image_url,
                category_id=item["product"].category_id,
                is_active=item["product"].is_active,
                created_at=item["product"].created_at,
                score=item["score"],
                rank=idx + 1,
            )
            for idx, (_, item) in enumerate(sorted_candidates)
            if item["product"] is not None
        ]

    def get_similar_products(
        self,
        product_id: int,
        k: int = 10,
    ) -> List[ProductWithScore]:
        """Get similar products based on co-occurrence with caching."""
        # Check cache first
        cache_key = f"sim:{product_id}:{k}"
        cached = cache_service.get(cache_key)
        if cached:
            return [ProductWithScore(**p) for p in cached]

        # Get from service
        similar = self.similarity_service.get_similar_products(product_id, k)

        # Cache result
        cache_service.set(
            cache_key,
            [p.model_dump() for p in similar],
            settings.cache_ttl_similar_products,
        )

        return similar

    def _cache_recommendations(
        self,
        cache_key: str,
        recommendations: List[ProductWithScore],
        strategy: str,
    ):
        """Cache recommendations with strategy info."""
        cache_service.set(
            cache_key,
            {
                "recommendations": [p.model_dump() for p in recommendations],
                "strategy": strategy,
            },
            settings.cache_ttl_recommendations,
        )
