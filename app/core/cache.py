"""
Redis cache utilities with enhanced functionality.
"""
import json
from typing import Any, Optional
import redis.asyncio as redis

from app.core.config import settings

# Redis client - lazy initialized to avoid event loop issues
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client (lazy initialization)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
    return _redis_client


# Backward compatibility alias
redis_client = property(lambda self: get_redis_client())


async def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    client = get_redis_client()
    value = await client.get(key)
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
    client = get_redis_client()
    # Serialize complex objects
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    
    await client.set(key, value, ex=expire)
    return True


async def delete_cache(key: str) -> bool:
    """
    Delete key from cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if deleted
    """
    client = get_redis_client()
    result = await client.delete(key)
    return result > 0


async def delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern.
    
    Args:
        pattern: Key pattern (e.g., "user:*")
        
    Returns:
        Number of keys deleted
    """
    client = get_redis_client()
    keys = []
    async for key in client.scan_iter(match=pattern):
        keys.append(key)
    
    if keys:
        return await client.delete(*keys)
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
    client = get_redis_client()
    return await client.incrby(key, amount)


async def get_ttl(key: str) -> int:
    """
    Get time to live for a key.
    
    Args:
        key: Cache key
        
    Returns:
        TTL in seconds, -1 if no expiry, -2 if key doesn't exist
    """
    client = get_redis_client()
    return await client.ttl(key)


def reset_redis_client():
    """Reset the Redis client (useful for testing)."""
    global _redis_client
    _redis_client = None


# Cache key generators
def user_permissions_key(user_id: str) -> str:
    """Generate cache key for user permissions."""
    return f"permissions:user:{user_id}"


def user_profile_key(user_id: str) -> str:
    """Generate cache key for user profile."""
    return f"user:profile:{user_id}"


def otp_key(email: str, otp_type: str) -> str:
    """Generate cache key for OTP."""
    return f"otp:{email}:{otp_type}"


def rate_limit_key(identifier: str, scope: str) -> str:
    """Generate cache key for rate limiting."""
    return f"rate_limit:{scope}:{identifier}"

