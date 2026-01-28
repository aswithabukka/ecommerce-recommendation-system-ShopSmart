from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.database import ItemSimilarity, Product
from app.models.schemas import ProductWithScore


class SimilarityService:
    """Service for item-to-item similarity based recommendations."""

    def __init__(self, db: Session):
        self.db = db

    def get_similar_products(
        self,
        product_id: int,
        k: int = 10,
    ) -> List[ProductWithScore]:
        """Get products similar to a given product based on co-occurrence."""
        # Get source product's category
        source_product = self.db.query(Product).filter(Product.id == product_id).first()
        if not source_product:
            return []

        # Fetch more candidates than needed to allow category filtering
        candidates = (
            self.db.query(ItemSimilarity, Product)
            .join(Product, ItemSimilarity.similar_product_id == Product.id)
            .filter(ItemSimilarity.product_id == product_id)
            .filter(Product.is_active == True)
            .order_by(desc(ItemSimilarity.similarity_score))
            .limit(k * 3)  # Get 3x more candidates
            .all()
        )

        # Prioritize same-category items by boosting their scores
        scored_products = []
        for similarity, product in candidates:
            score = similarity.similarity_score
            # Boost same-category items by 20%
            if product.category_id == source_product.category_id:
                score = score * 1.2
            scored_products.append((similarity, product, score))

        # Re-sort by adjusted scores and take top k
        scored_products.sort(key=lambda x: x[2], reverse=True)
        top_k = scored_products[:k]

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
                score=similarity.similarity_score,  # Use original score for display
                rank=idx + 1,
            )
            for idx, (similarity, product, _) in enumerate(top_k)
        ]

    def get_similar_products_for_multiple(
        self,
        product_ids: List[int],
        k: int = 10,
        exclude_ids: set = None,
    ) -> dict:
        """
        Get similar products for multiple source products.
        Returns a dict mapping product_id -> list of similar products.
        """
        if exclude_ids is None:
            exclude_ids = set()

        # Include source products in exclusion
        exclude_ids = exclude_ids | set(product_ids)

        similar = (
            self.db.query(ItemSimilarity, Product)
            .join(Product, ItemSimilarity.similar_product_id == Product.id)
            .filter(ItemSimilarity.product_id.in_(product_ids))
            .filter(~ItemSimilarity.similar_product_id.in_(exclude_ids))
            .filter(Product.is_active == True)
            .order_by(ItemSimilarity.product_id, desc(ItemSimilarity.similarity_score))
            .all()
        )

        result = {}
        for similarity, product in similar:
            source_id = similarity.product_id
            if source_id not in result:
                result[source_id] = []
            if len(result[source_id]) < k:
                result[source_id].append(
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
                        score=similarity.similarity_score,
                        rank=len(result[source_id]) + 1,
                    )
                )

        return result
