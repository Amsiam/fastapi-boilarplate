"""
Rate limiting middleware and utilities.
Uses Redis-based sliding window rate limiting.
"""
from functools import wraps
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.cache import get_redis_client
from app.constants import ErrorCode


class RateLimitExceeded(HTTPException):
    """Rate limit exceeded exception."""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": {
                    "code": ErrorCode.RATE_LIMIT_EXCEEDED,
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "field": None
                },
                "details": {"retry_after": retry_after}
            },
            headers={"Retry-After": str(retry_after)}
        )


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for forwarded headers (for reverse proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in the list is the original client
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    return "unknown"


async def check_rate_limit(
    identifier: str,
    limit: int,
    window: int,
    scope: str = "default"
) -> tuple[bool, int, int]:
    """
    Check if rate limit is exceeded using sliding window algorithm.
    
    Args:
        identifier: Unique identifier (IP, user_id, etc.)
        limit: Maximum requests allowed
        window: Time window in seconds
        scope: Namespace for the rate limit
        
    Returns:
        Tuple of (is_allowed, remaining, retry_after)
    """
    import time
    
    client = get_redis_client()
    key = f"rate_limit:{scope}:{identifier}"
    now = time.time()
    window_start = now - window
    
    # Use Redis pipeline for atomic operations
    pipe = client.pipeline()
    
    # Remove old entries outside the window
    pipe.zremrangebyscore(key, 0, window_start)
    
    # Count current requests in window
    pipe.zcard(key)
    
    # Add current request
    pipe.zadd(key, {str(now): now})
    
    # Set expiry on the key
    pipe.expire(key, window)
    
    results = await pipe.execute()
    current_count = results[1]
    
    if current_count >= limit:
        # Calculate retry after
        oldest = await client.zrange(key, 0, 0, withscores=True)
        if oldest:
            retry_after = int(window - (now - oldest[0][1])) + 1
        else:
            retry_after = window
        return False, 0, retry_after
    
    remaining = limit - current_count - 1
    return True, remaining, 0


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    # Auth endpoints - strict limits
    "auth:login": {"limit": 5, "window": 60},
    "auth:register": {"limit": 3, "window": 60},
    "auth:forgot_password": {"limit": 3, "window": 300},
    "auth:reset_password": {"limit": 3, "window": 300},
    "auth:verify_email": {"limit": 5, "window": 60},
    "auth:resend_otp": {"limit": 3, "window": 60},
    "auth:change_password": {"limit": 3, "window": 300},
    
    # Admin write operations
    "admin:write": {"limit": 30, "window": 60},
    
    # Admin read operations
    "admin:read": {"limit": 100, "window": 60},
    
    # OAuth
    "oauth:login": {"limit": 10, "window": 60},
    
    # Default fallback
    "default": {"limit": 60, "window": 60},
}


def rate_limit(scope: str = "default", by: str = "ip"):
    """
    Decorator for endpoint-specific rate limiting.
    
    Args:
        scope: Rate limit scope (must be defined in RATE_LIMITS)
        by: Identifier type - "ip" or "user"
    
    Usage:
        @router.post("/login")
        @rate_limit("auth:login")
        async def login(request: Request, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import os
            
            # Skip rate limiting in tests
            if os.environ.get("TESTING") == "1":
                return await func(*args, **kwargs)

            # Find request in args or kwargs
            request_obj = None
            
            # First check kwargs for common names, but verify type
            for key in ["request", "req", "http_request"]:
                if key in kwargs and isinstance(kwargs[key], Request):
                    request_obj = kwargs[key]
                    break
            
            # If not found, search all kwargs values
            if request_obj is None:
                for val in kwargs.values():
                    if isinstance(val, Request):
                        request_obj = val
                        break
            
            # If not found, search args
            if request_obj is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request_obj = arg
                        break
            
            if request_obj is None:
                # Can't rate limit without request
                return await func(*args, **kwargs)
            
            # Get identifier
            if by == "user":
                # Check for current_user in kwargs
                current_user = kwargs.get("current_user")
                if current_user:
                    identifier = str(current_user.id)
                else:
                    identifier = get_client_ip(request_obj)
            else:
                identifier = get_client_ip(request_obj)
            
            # Get rate limit config
            config = RATE_LIMITS.get(scope, RATE_LIMITS["default"])
            
            # Check rate limit
            is_allowed, remaining, retry_after = await check_rate_limit(
                identifier=identifier,
                limit=config["limit"],
                window=config["window"],
                scope=scope
            )
            
            if not is_allowed:
                raise RateLimitExceeded(retry_after=retry_after)
            
            # Add rate limit headers to response
            response = await func(*args, **kwargs)
            
            return response
        
        return wrapper
    return decorator


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware.
    Applies default rate limit to all requests.
    Disabled during tests (when TESTING env var is set).
    """
    
    def __init__(self, app, limit: int = 60, window: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window
    
    async def dispatch(self, request: Request, call_next):
        import os
        
        # Skip rate limiting in tests
        if os.environ.get("TESTING") == "1":
            return await call_next(request)
        
        # Skip health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        identifier = get_client_ip(request)
        
        is_allowed, remaining, retry_after = await check_rate_limit(
            identifier=identifier,
            limit=self.limit,
            window=self.window,
            scope="global"
        )
        
        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": ErrorCode.RATE_LIMIT_EXCEEDED,
                        "message": f"Too many requests. Please try again in {retry_after} seconds.",
                        "field": None
                    },
                    "details": {"retry_after": retry_after}
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after)
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
