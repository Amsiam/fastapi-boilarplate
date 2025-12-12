"""
Basic authentication tests.
Run with: pytest tests/test_auth.py -v
"""
import pytest
import uuid


@pytest.fixture
async def test_user_data():
    """Test user data with unique email per test run."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"test_{unique_id}@example.com",
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
    
    async def test_register_weak_password(self, client, test_user_data):
        """Test registration with weak password."""
        test_user_data["password"] = "123"
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 422
    
    async def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = await client.post("/api/v1/auth/register", json={"email": "test@example.com"})
        
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
            json={"username": test_user_data["email"], "password": test_user_data["password"]}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTH_002"
    
    async def test_login_invalid_credentials(self, client, test_user_data):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": test_user_data["email"], "password": "WrongPassword123!"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTH_001"
    
    async def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "test@example.com"}
        )
        
        assert response.status_code == 422


class TestOTP:
    """Test OTP functionality."""
    
    async def test_otp_rate_limiting(self, client):
        """Test OTP rate limiting."""
        unique_id = str(uuid.uuid4())[:8]
        email = f"ratelimit_{unique_id}@example.com"
        
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
    
    async def test_otp_invalid_type(self, client):
        """Test OTP with invalid type."""
        response = await client.post(
            "/api/v1/auth/resend-otp",
            json={"email": "test@example.com", "type": "INVALID_TYPE"}
        )
        
        assert response.status_code == 422


class TestTokens:
    """Test JWT token functionality."""
    
    async def test_access_protected_route_without_token(self, client):
        """Test accessing protected route without token."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    async def test_access_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401


class TestRefreshToken:
    """Test refresh token functionality."""
    
    async def test_refresh_missing_body(self, client):
        """Test refresh endpoint without body."""
        response = await client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 422



