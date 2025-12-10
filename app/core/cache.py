"""
Redis cache utilities with enhanced functionality.
"""
import json
from typing import Any, Optional
import redis.asyncio as redis

from app.core.config import settings

# Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)


async def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    value = await redis_client.get(key)
    if value:
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return None


async def set_cache(
    key: str,
    value: Any,
    expire: int = 300  # 5 minutes default
) -> bool:
    """
    Set value in cache.
    
    Args:
        key: Cache key
        value: Value to cache
        expire: Expiration time in seconds
        
    Returns:
        True if successful
    """
    # Serialize complex objects
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    
    await redis_client.set(key, value, ex=expire)
    return True


async def delete_cache(key: str) -> bool:
    """
    Delete key from cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if deleted
    """
    result = await redis_client.delete(key)
    return result > 0


async def delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern.
    
    Args:
        pattern: Key pattern (e.g., "user:*")
        
    Returns:
        Number of keys deleted
    """
    keys = []
    async for key in redis_client.scan_iter(match=pattern):
        keys.append(key)
    
    if keys:
        return await redis_client.delete(*keys)
    return 0


async def increment_cache(key: str, amount: int = 1) -> int:
    """
    Increment a counter.
    
    Args:
        key: Cache key
        amount: Amount to increment
        
    Returns:
        New value
    """
    return await redis_client.incrby(key, amount)


async def get_ttl(key: str) -> int:
    """
    Get time to live for a key.
    
    Args:
        key: Cache key
        
    Returns:
        TTL in seconds, -1 if no expiry, -2 if key doesn't exist
    """
    return await redis_client.ttl(key)


# Cache key generators
def user_permissions_key(user_id: str) -> str:
    """Generate cache key for user permissions."""
    return f"permissions:user:{user_id}"


def otp_key(email: str, otp_type: str) -> str:
    """Generate cache key for OTP."""
    return f"otp:{email}:{otp_type}"


def rate_limit_key(identifier: str, scope: str) -> str:
    """Generate cache key for rate limiting."""
    return f"rate_limit:{scope}:{identifier}"
