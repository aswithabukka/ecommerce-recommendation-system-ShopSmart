from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.database import Product, Category


class ProductService:
    """Service for product operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_product(self, product_id: int) -> Optional[Product]:
        """Get a single product by ID."""
        return self.db.query(Product).filter(
            Product.id == product_id,
            Product.is_active == True
        ).first()

    def get_products_by_ids(self, product_ids: List[int]) -> List[Product]:
        """Get multiple products by their IDs."""
        return self.db.query(Product).filter(
            Product.id.in_(product_ids),
            Product.is_active == True
        ).all()

    def search_products(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Product], int]:
        """Search and filter products with pagination."""
        query = self.db.query(Product).filter(Product.is_active == True)

        # Apply search filter (using trigram similarity for fuzzy search)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.description.ilike(search_pattern),
                )
            )

        # Apply category filter
        if category:
            category_obj = self.db.query(Category).filter(
                Category.name.ilike(f"%{category}%")
            ).first()
            if category_obj:
                query = query.filter(Product.category_id == category_obj.id)

        # Apply price range filter
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # Apply rating filter
        # Note: average_rating column removed from schema
        # if min_rating is not None:
        #     query = query.filter(Product.average_rating >= min_rating)

        # Get total count
        total = query.count()

        # Apply pagination - order by most recent first
        offset = (page - 1) * page_size
        products = query.order_by(Product.created_at.desc(), Product.id).offset(offset).limit(page_size).all()

        return products, total

    def get_products_by_category(
        self,
        category_id: int,
        limit: int = 20,
    ) -> List[Product]:
        """Get products in a specific category."""
        return self.db.query(Product).filter(
            Product.category_id == category_id,
            Product.is_active == True
        ).limit(limit).all()

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """Get category by name."""
        return self.db.query(Category).filter(
            Category.name.ilike(f"%{name}%")
        ).first()
