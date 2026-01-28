from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.database import Event, User, Product
from app.core.redis import cache_service


class EventService:
    """Service for handling user events."""

    def __init__(self, db: Session):
        self.db = db

    def product_exists(self, product_id: int) -> bool:
        """Check if a product exists."""
        return self.db.query(Product).filter(Product.id == product_id).first() is not None

    def get_or_create_user(self, external_id: str) -> User:
        """Get existing user or create a new one."""
        user = self.db.query(User).filter(User.external_id == external_id).first()

        if not user:
            user = User(
                external_id=external_id,
                is_anonymous=True,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        return user

    def create_event(
        self,
        user_id: int,
        product_id: int,
        event_type: str,
        timestamp: datetime = None,
        session_id: str = None,
        metadata: Dict[str, Any] = None,
    ) -> Event:
        """Create a new event and invalidate user's recommendation cache."""
        event = Event(
            user_id=user_id,
            product_id=product_id,
            event_type=event_type,
            timestamp=timestamp or datetime.utcnow(),
            session_id=session_id,
            metadata=metadata,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # Invalidate user's recommendation cache
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            cache_service.invalidate_user_recommendations(user.external_id)

        return event

    def get_user_events(
        self,
        user_id: int,
        limit: int = 50,
        event_types: list = None,
    ) -> list:
        """Get recent events for a user."""
        query = self.db.query(Event).filter(Event.user_id == user_id)

        if event_types:
            query = query.filter(Event.event_type.in_(event_types))

        return query.order_by(Event.timestamp.desc()).limit(limit).all()

    def get_user_interacted_products(self, user_id: int, limit: int = 50) -> set:
        """Get set of product IDs the user has interacted with."""
        events = self.get_user_events(user_id, limit)
        return {e.product_id for e in events}
