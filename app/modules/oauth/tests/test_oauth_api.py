
import pytest
from unittest.mock import patch, AsyncMock


class TestOAuth:
    """Test OAuth endpoints."""
    
    async def test_list_providers(self, client):
        """Test listing OAuth providers."""
        response = await client.get("/api/v1/auth/oauth/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Allow empty list if no providers are seeded
        assert isinstance(data["data"], list)
        
    async def test_get_login_url(self, client, session):
        """Test generating login URL."""
        # First seed a provider for testing
        from app.modules.oauth.models import OAuthProvider
        provider = OAuthProvider(
            name="google",
            display_name="Google",
            client_id="test-client-id",
            client_secret="test-client-secret",
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
            scopes=["openid", "email", "profile"],
            is_active=True
        )
        session.add(provider)
        await session.commit()
        
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

    @patch("app.modules.oauth.endpoints.OAuthService")
    async def test_oauth_callback_success(self, mock_service_cls, client):
        """Test successful OAuth callback (mocked)."""
        # Setup mock with AsyncMock for the async method
        mock_service = mock_service_cls.return_value
        mock_service.handle_callback = AsyncMock(return_value={
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "token_type": "bearer"
        })
        
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
