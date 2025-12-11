"""
Cache and utility tests.
Run with: pytest tests/test_cache.py -v
"""
import pytest
from app.core.cache import (
    get_redis_client,
    reset_redis_client,
    get_cache,
    set_cache,
    delete_cache,
    increment_cache,
    user_permissions_key,
    otp_key,
    rate_limit_key
)


class TestCacheKeyGenerators:
    """Test cache key generator functions."""
    
    def test_user_permissions_key(self):
        """Test user permissions key generation."""
        key = user_permissions_key("user-123")
        assert key == "permissions:user:user-123"
    
    def test_otp_key(self):
        """Test OTP key generation."""
        key = otp_key("test@example.com", "EMAIL_VERIFICATION")
        assert key == "otp:test@example.com:EMAIL_VERIFICATION"
    
    def test_rate_limit_key(self):
        """Test rate limit key generation."""
        key = rate_limit_key("user@example.com", "login")
        assert key == "rate_limit:login:user@example.com"


class TestRedisClient:
    """Test Redis client management."""
    
    def test_reset_redis_client(self):
        """Test resetting Redis client."""
        # Get client first
        client1 = get_redis_client()
        assert client1 is not None
        
        # Reset
        reset_redis_client()
        
        # New client should be created
        client2 = get_redis_client()
        assert client2 is not None
    
    def test_get_redis_client_singleton(self):
        """Test that get_redis_client returns same instance."""
        reset_redis_client()
        client1 = get_redis_client()
        client2 = get_redis_client()
        assert client1 is client2


class TestCacheOperations:
    """Test cache operations."""
    
    async def test_set_and_get_string(self):
        """Test setting and getting a string value."""
        reset_redis_client()
        await set_cache("test:string", "hello", expire=60)
        value = await get_cache("test:string")
        assert value == "hello"
        await delete_cache("test:string")
    
    async def test_set_and_get_dict(self):
        """Test setting and getting a dict value."""
        reset_redis_client()
        test_data = {"key": "value", "number": 42}
        await set_cache("test:dict", test_data, expire=60)
        value = await get_cache("test:dict")
        assert value == test_data
        await delete_cache("test:dict")
    
    async def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        reset_redis_client()
        value = await get_cache("nonexistent:key:12345")
        assert value is None
    
    async def test_delete_cache(self):
        """Test deleting a cache key."""
        reset_redis_client()
        await set_cache("test:delete", "value", expire=60)
        result = await delete_cache("test:delete")
        assert result is True
        
        # Key should be gone
        value = await get_cache("test:delete")
        assert value is None
    
    async def test_increment_cache(self):
        """Test incrementing a counter."""
        reset_redis_client()
        # Delete first to ensure clean state
        await delete_cache("test:counter")
        
        # Increment from 0
        result = await increment_cache("test:counter", 1)
        assert result == 1
        
        # Increment again
        result = await increment_cache("test:counter", 5)
        assert result == 6
        
        await delete_cache("test:counter")
