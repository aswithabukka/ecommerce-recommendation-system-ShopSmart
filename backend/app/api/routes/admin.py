from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.core.redis import cache_service
from app.config import settings
from app.models.database import Event, User, Product, DailyEventStats
from app.models.schemas import AdminDashboardResponse, DailyEventStatsResponse
from app.services.trending_service import TrendingService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(db: Session = Depends(get_db)):
    """
    Get admin dashboard data including:
    - Events by day (last 7 days)
    - Top trending products
    - API stats summary
    - Total counts
    """
    # Check cache
    cache_key = "admin:dashboard"
    cached = cache_service.get(cache_key)
    if cached:
        return AdminDashboardResponse(**cached)

    # Get events by day (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # Check if we have pre-computed daily stats
    daily_stats = (
        db.query(DailyEventStats)
        .filter(DailyEventStats.date >= seven_days_ago.date())
        .order_by(DailyEventStats.date.desc())
        .all()
    )

    if not daily_stats:
        # Compute on the fly if no pre-computed stats
        daily_stats = _compute_daily_stats(db, seven_days_ago)

    events_by_day = [
        DailyEventStatsResponse(
            date=stat.date if hasattr(stat, 'date') else stat['date'],
            event_type=stat.event_type if hasattr(stat, 'event_type') else stat['event_type'],
            event_count=stat.event_count if hasattr(stat, 'event_count') else stat['event_count'],
            unique_users=stat.unique_users if hasattr(stat, 'unique_users') else stat['unique_users'],
            unique_products=stat.unique_products if hasattr(stat, 'unique_products') else stat['unique_products'],
        )
        for stat in daily_stats
    ]

    # Get top trending products
    trending_service = TrendingService(db)
    top_trending = trending_service.get_trending_products_raw(k=10, time_window="7d")

    # Get total counts
    total_events = db.query(func.count(Event.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0

    # Build response
    response = AdminDashboardResponse(
        events_by_day=events_by_day,
        top_trending=top_trending,
        api_stats={"note": "API stats tracking not yet implemented"},
        total_events=total_events,
        total_users=total_users,
        total_products=total_products,
    )

    # Cache response
    cache_service.set(cache_key, response.model_dump(), settings.cache_ttl_admin)

    return response


@router.post("/cache/flush")
async def flush_cache():
    """Flush all cache entries."""
    count = cache_service.invalidate_all()
    return {"message": f"Flushed {count} cache entries"}


@router.post("/cache/flush/recommendations")
async def flush_recommendations_cache():
    """Flush recommendation cache entries."""
    count = cache_service.delete_pattern("rec:*")
    return {"message": f"Flushed {count} recommendation cache entries"}


@router.post("/cache/flush/similar")
async def flush_similar_cache():
    """Flush similar products cache entries."""
    count = cache_service.invalidate_similar_products()
    return {"message": f"Flushed {count} similar products cache entries"}


@router.post("/cache/flush/trending")
async def flush_trending_cache():
    """Flush trending cache entries."""
    count = cache_service.invalidate_trending()
    return {"message": f"Flushed {count} trending cache entries"}


def _compute_daily_stats(db: Session, since: datetime) -> List[dict]:
    """Compute daily event stats on the fly."""
    stats = (
        db.query(
            func.date(Event.timestamp).label("date"),
            Event.event_type,
            func.count(Event.id).label("event_count"),
            func.count(func.distinct(Event.user_id)).label("unique_users"),
            func.count(func.distinct(Event.product_id)).label("unique_products"),
        )
        .filter(Event.timestamp >= since)
        .group_by(func.date(Event.timestamp), Event.event_type)
        .order_by(func.date(Event.timestamp).desc())
        .all()
    )

    return [
        {
            "date": datetime.combine(row.date, datetime.min.time()),
            "event_type": row.event_type,
            "event_count": row.event_count,
            "unique_users": row.unique_users,
            "unique_products": row.unique_products,
        }
        for row in stats
    ]
