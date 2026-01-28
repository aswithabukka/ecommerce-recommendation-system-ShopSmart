from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.schemas import RecommendationResponse, SimilarProductsResponse
from app.services.recommendation_service import RecommendationService
from app.services.product_service import ProductService

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: str = Query(..., description="User ID or session ID"),
    k: int = Query(default=10, ge=1, le=100, description="Number of recommendations"),
    category_id: Optional[int] = Query(default=None, description="Filter by category ID"),
    db: Session = Depends(get_db),
):
    """
    Get personalized recommendations for a user.

    Strategy selection:
    1. If user has interaction history -> Item-to-item collaborative filtering (personalized)
    2. If no history but category specified -> Trending by category (cold start)
    3. If no history and no category -> Global trending
    """
    rec_service = RecommendationService(db)

    recommendations, strategy = rec_service.get_recommendations(
        user_id=user_id,
        k=k,
        category_id=category_id,
    )

    return RecommendationResponse(
        user_id=user_id,
        recommendations=recommendations,
        strategy=strategy,
        generated_at=datetime.utcnow(),
    )


@router.get("/similar-products", response_model=SimilarProductsResponse)
async def get_similar_products(
    product_id: int = Query(..., description="Source product ID"),
    k: int = Query(default=10, ge=1, le=100, description="Number of similar products"),
    db: Session = Depends(get_db),
):
    """
    Get products similar to the given product based on co-occurrence patterns.

    Returns products that users frequently viewed/purchased together.
    """
    # Verify product exists
    product_service = ProductService(db)
    product = product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    rec_service = RecommendationService(db)

    similar_products = rec_service.get_similar_products(
        product_id=product_id,
        k=k,
    )

    return SimilarProductsResponse(
        product_id=product_id,
        similar_products=similar_products,
        generated_at=datetime.utcnow(),
    )
