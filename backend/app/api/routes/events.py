from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.schemas import EventCreate, EventResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """
    Track a user event (view, add_to_cart, purchase).

    - **user_id**: External user identifier or session ID
    - **product_id**: Product ID from catalog
    - **event_type**: One of 'view', 'add_to_cart', 'purchase'
    - **timestamp**: Optional, defaults to current time
    - **session_id**: Optional browser session ID
    - **metadata**: Optional additional event data
    """
    event_service = EventService(db)

    # Validate product exists
    if not event_service.product_exists(event.product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {event.product_id} not found",
        )

    # Get or create user
    user = event_service.get_or_create_user(event.user_id)

    # Create event
    db_event = event_service.create_event(
        user_id=user.id,
        product_id=event.product_id,
        event_type=event.event_type,
        timestamp=event.timestamp or datetime.utcnow(),
        session_id=event.session_id,
        metadata=event.metadata,
    )

    return db_event
