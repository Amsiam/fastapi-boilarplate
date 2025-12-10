"""
Response caching utilities for read-heavy endpoints.
Uses Redis for distributed caching.
"""
from functools import wraps
from typing import Callable, Optional
import hashlib
import json

from fastapi import Request
from starlette.responses import JSONResponse

from app.core.cache import get_cache, set_cache, delete_pattern


def cache_key_from_request(request: Request, prefix: str) -> str:
    """
    Generate a cache key from request path and query params.
    
    Args:
        request: FastAPI request
        prefix: Cache key prefix
        
    Returns:
        Cache key string
    """
    # Include path and sorted query params
    query_str = str(sorted(request.query_params.items()))
    key_data = f"{request.url.path}:{query_str}"
    key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
    return f"response_cache:{prefix}:{key_hash}"


def cache_response(
    prefix: str,
    expire: int = 300,
    vary_on_user: bool = False
):
    """
    Decorator to cache endpoint responses.
    
    Args:
        prefix: Cache key prefix (e.g., "permissions", "roles")
        expire: Cache TTL in seconds (default: 5 minutes)
        vary_on_user: If True, cache separately per user
    
    Usage:
        @router.get("/permissions")
        @cache_response("permissions", expire=300)
        async def list_permissions(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args or kwargs
            request = kwargs.get("request") or kwargs.get("req")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            # Generate cache key
            if request:
                cache_key = cache_key_from_request(request, prefix)
                
                # Add user ID to key if vary_on_user
                if vary_on_user:
                    current_user = kwargs.get("current_user")
                    if current_user:
                        cache_key = f"{cache_key}:user:{current_user.id}"
            else:
                cache_key = f"response_cache:{prefix}:default"
            
            # Check cache
            cached = await get_cache(cache_key)
            if cached is not None:
                # Return cached response
                return JSONResponse(
                    content=cached,
                    headers={"X-Cache": "HIT"}
                )
            
            # Execute function
            response = await func(*args, **kwargs)
            
            # Cache the response data
            if hasattr(response, 'model_dump'):
                # Pydantic model
                response_data = response.model_dump()
            elif hasattr(response, 'body'):
                # Starlette Response
                response_data = json.loads(response.body)
            elif isinstance(response, dict):
                response_data = response
            else:
                # Try to serialize
                try:
                    response_data = json.loads(json.dumps(response, default=str))
                except:
                    # Can't cache this response
                    return response
            
            await set_cache(cache_key, response_data, expire=expire)
            
            return response
        
        return wrapper
    return decorator


async def invalidate_cache(prefix: str) -> int:
    """
    Invalidate all cached responses for a prefix.
    
    Args:
        prefix: Cache key prefix to invalidate
        
    Returns:
        Number of keys deleted
    """
    pattern = f"response_cache:{prefix}:*"
    return await delete_pattern(pattern)


# Cache configurations for different resources
CACHE_CONFIG = {
    "permissions": {"expire": 300, "vary_on_user": False},  # 5 min, same for all
    "roles": {"expire": 120, "vary_on_user": False},  # 2 min
    "oauth_providers": {"expire": 300, "vary_on_user": False},  # 5 min
}
