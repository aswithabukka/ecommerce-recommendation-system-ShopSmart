from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.core.database import get_db
from app.models.database import Category, Product
from app.models.schemas import ProductSearchResponse, ProductResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductSearchResponse)
async def search_products(
    search: Optional[str] = Query(default=None, description="Search query for product name/description"),
    category: Optional[str] = Query(default=None, description="Filter by category name"),
    min_price: Optional[float] = Query(default=None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(default=None, ge=0, description="Maximum price"),
    min_rating: Optional[float] = Query(default=None, ge=1, le=5, description="Minimum average rating"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Search and filter products.

    - **search**: Full-text search on product name and description
    - **category**: Filter by category name (case-insensitive)
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **min_rating**: Minimum average rating (1-5 stars)
    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (max 100)
    """
    product_service = ProductService(db)

    products, total = product_service.search_products(
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        page=page,
        page_size=page_size,
    )

    return ProductSearchResponse(
        products=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get("/categories", response_model=List[dict])
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories with product counts."""
    categories = (
        db.query(
            Category.id,
            Category.name,
            func.count(Product.id).label("product_count")
        )
        .outerjoin(Product, Category.id == Product.category_id)
        .filter(Product.is_active == True)
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
        .all()
    )

    return [
        {
            "id": cat.id,
            "name": cat.name,
            "product_count": cat.product_count
        }
        for cat in categories
    ]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID."""
    product_service = ProductService(db)
    product = product_service.get_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductResponse.model_validate(product)
