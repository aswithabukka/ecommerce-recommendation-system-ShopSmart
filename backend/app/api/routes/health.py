from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.core.database import get_db
from app.core.redis import redis_client
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Check the health of the API and its dependencies.

    Returns status of:
    - API server
    - PostgreSQL database
    - Redis cache
    """
    # Check database
    try:
        db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    # Overall status
    if database_status == "healthy" and redis_status == "healthy":
        status = "healthy"
    else:
        status = "degraded"

    return HealthResponse(
        status=status,
        database=database_status,
        redis=redis_status,
        timestamp=datetime.utcnow(),
    )
