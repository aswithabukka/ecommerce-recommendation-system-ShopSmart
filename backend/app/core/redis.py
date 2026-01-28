import redis
import json
from typing import Optional, Any
from functools import wraps
from datetime import timedelta

from app.config import settings


# Create Redis client
redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def get_redis() -> redis.Redis:
    """Dependency to get Redis client."""
    return redis_client


class CacheService:
    """Service for caching with Redis."""

    def __init__(self, client: redis.Redis = None):
        self.client = client or redis_client

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except (redis.RedisError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL in seconds."""
        try:
            self.client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except (redis.RedisError, TypeError):
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            self.client.delete(key)
            return True
        except redis.RedisError:
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except redis.RedisError:
            return 0

    def invalidate_user_recommendations(self, user_id: str) -> int:
        """Invalidate all cached recommendations for a user."""
        return self.delete_pattern(f"rec:{user_id}:*")

    def invalidate_similar_products(self, product_id: int = None) -> int:
        """Invalidate cached similar products."""
        if product_id:
            return self.delete_pattern(f"sim:{product_id}:*")
        return self.delete_pattern("sim:*")

    def invalidate_trending(self) -> int:
        """Invalidate cached trending products."""
        return self.delete_pattern("trending:*")

    def invalidate_all(self) -> int:
        """Invalidate all cache."""
        return self.delete_pattern("*")


# Default cache service instance
cache_service = CacheService()


def cached(key_prefix: str, ttl: int = 300):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from arguments
            cache_key = f"{key_prefix}:{':'.join(str(v) for v in args)}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"

            # Try to get from cache
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
