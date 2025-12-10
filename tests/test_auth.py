"""
Basic authentication tests.
Run with: pytest tests/test_auth.py -v
"""
import pytest
from httpx import AsyncClient
from sqlmodel import select
from app.main import app
from app.models.user import User
from app.core.database import async_session_maker


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890"
    }


class TestRegistration:
    """Test user registration flow."""
    
    async def test_register_success(self, client, test_user_data):
        """Test successful user registration."""
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "verify your email" in data["message"].lower()
    
    async def test_register_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email."""
        # Register first time
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register again
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "USER_002"
    
    async def test_register_invalid_email(self, client, test_user_data):
        """Test registration with invalid email."""
        test_user_data["email"] = "invalid-email"
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 422


class TestLogin:
    """Test login flow."""
    
    async def test_login_unverified_user(self, client, test_user_data):
        """Test login with unverified email."""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to login without verifying
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user_data["email"], "password": test_user_data["password"]}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTH_002"
    
    async def test_login_invalid_credentials(self, client, test_user_data):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user_data["email"], "password": "WrongPassword123!"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTH_001"


class TestOTP:
    """Test OTP functionality."""
    
    async def test_otp_rate_limiting(self, client):
        """Test OTP rate limiting."""
        email = "ratelimit@example.com"
        
        # First request should succeed
        response1 = await client.post(
            "/api/v1/auth/resend-otp",
            json={"email": email, "type": "EMAIL_VERIFICATION"}
        )
        assert response1.status_code == 200
        
        # Immediate second request should fail (cooldown)
        response2 = await client.post(
            "/api/v1/auth/resend-otp",
            json={"email": email, "type": "EMAIL_VERIFICATION"}
        )
        assert response2.status_code == 429
        data = response2.json()
        assert data["error"]["code"] == "OTP_004"


class TestTokens:
    """Test JWT token functionality."""
    
    async def test_access_protected_route_without_token(self, client):
        """Test accessing protected route without token."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False


class TestPasswordReset:
    """Test password reset flow."""
    
    async def test_forgot_password(self, client):
        """Test forgot password request."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"}
        )
        
        # Should always return success (security)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# Run tests with:
# pytest tests/test_auth.py -v --asyncio-mode=auto
