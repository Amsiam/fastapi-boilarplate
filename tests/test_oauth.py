
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from app.main import app

class TestOAuth:
    """Test OAuth endpoints."""
    
    async def test_list_providers(self, client):
        """Test listing OAuth providers."""
        response = await client.get("/api/v1/auth/oauth/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 2
        
        providers = {p["name"] for p in data["data"]}
        assert "google" in providers
        assert "github" in providers
        
    async def test_get_login_url(self, client):
        """Test generating login URL."""
        response = await client.get(
            "/api/v1/auth/oauth/login/google",
            params={"redirect_uri": "http://localhost:3000/callback"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "url" in data["data"]
        assert "https://accounts.google.com" in data["data"]["url"]
        assert "client_id" in data["data"]["url"]
        assert "redirect_uri" in data["data"]["url"]
        
    async def test_get_login_url_invalid_provider(self, client):
        """Test generating login URL for invalid provider."""
        response = await client.get(
            "/api/v1/auth/oauth/login/invalid-provider",
            params={"redirect_uri": "http://localhost:3000/callback"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "OAUTH_003"

    @patch("app.api.v1.endpoints.oauth.OAuthService")
    async def test_oauth_callback_success(self, mock_service_cls, client):
        """Test successful OAuth callback (mocked)."""
        # Setup mock
        mock_service = mock_service_cls.return_value
        mock_service.handle_callback.return_value = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "token_type": "bearer",
            "user": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "test@example.com",
                "is_active": True,
                "is_verified": True,
                "role": "CUSTOMER",
                "created_at": "2023-01-01T00:00:00Z"
            },
            "is_new": True
        }
        
        # Make request
        payload = {
            "provider": "google",
            "code": "mock_auth_code",
            "redirect_uri": "http://localhost:3000/callback"
        }
        response = await client.post("/api/v1/auth/oauth/callback", json=payload)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["access_token"] == "mock_access_token"
        
        # Verify mock called correctly
        mock_service.handle_callback.assert_called_once_with(
            provider_name="google",
            code="mock_auth_code",
            redirect_uri="http://localhost:3000/callback"
        )
