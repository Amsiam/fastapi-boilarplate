"""
OAuth Provider admin endpoint tests.
Run with: pytest tests/test_oauth_providers.py -v
"""
import pytest
import uuid


class TestOAuthProviderEndpointsUnauthorized:
    """Test OAuth provider endpoints without authentication."""
    
    async def test_list_providers_unauthorized(self, client):
        """Test listing providers without authentication."""
        response = await client.get("/api/v1/admin/oauth-providers")
        assert response.status_code == 401
    
    async def test_create_provider_unauthorized(self, client):
        """Test creating provider without authentication."""
        response = await client.post(
            "/api/v1/admin/oauth-providers",
            json={
                "name": "test_provider",
                "display_name": "Test Provider",
                "client_id": "client123",
                "client_secret": "secret123",
                "authorization_url": "https://example.com/auth",
                "token_url": "https://example.com/token",
                "user_info_url": "https://example.com/userinfo"
            }
        )
        assert response.status_code == 401
    
    async def test_get_provider_unauthorized(self, client):
        """Test getting provider without authentication."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/admin/oauth-providers/{fake_id}")
        assert response.status_code == 401
    
    async def test_update_provider_unauthorized(self, client):
        """Test updating provider without authentication."""
        fake_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/v1/admin/oauth-providers/{fake_id}",
            json={"display_name": "Updated Name"}
        )
        assert response.status_code == 401
    
    async def test_delete_provider_unauthorized(self, client):
        """Test deleting provider without authentication."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/v1/admin/oauth-providers/{fake_id}")
        assert response.status_code == 401
    
    async def test_update_status_unauthorized(self, client):
        """Test updating provider status without authentication."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(
            f"/api/v1/admin/oauth-providers/{fake_id}/status",
            json={"is_active": False}
        )
        assert response.status_code == 401


class TestOAuthProviderValidation:
    """Test OAuth provider endpoint validation."""
    
    async def test_create_provider_missing_fields(self, client):
        """Test creating provider with missing fields returns 401 (auth first)."""
        response = await client.post(
            "/api/v1/admin/oauth-providers",
            json={"name": "test"}
        )
        # Auth is checked before validation
        assert response.status_code == 401
    
    async def test_get_provider_invalid_uuid(self, client):
        """Test getting provider with invalid UUID returns 401 first."""
        response = await client.get("/api/v1/admin/oauth-providers/not-a-uuid")
        # Auth is checked before path validation
        assert response.status_code == 401


class TestOAuthProviderSchemas:
    """Test OAuth provider request schemas."""
    
    def test_create_request_valid(self):
        """Test valid create request schema."""
        from app.modules.oauth.schemas import OAuthProviderCreateRequest
        
        data = OAuthProviderCreateRequest(
            name="github",
            display_name="GitHub",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            user_info_url="https://api.github.com/user",
            scopes=["read:user", "user:email"]
        )
        
        assert data.name == "github"
        assert data.scopes == ["read:user", "user:email"]
    
    def test_create_request_defaults(self):
        """Test create request with defaults."""
        from app.modules.oauth.schemas import OAuthProviderCreateRequest
        
        data = OAuthProviderCreateRequest(
            name="test",
            display_name="Test",
            client_id="client",
            client_secret="secret",
            authorization_url="https://example.com/auth",
            token_url="https://example.com/token",
            user_info_url="https://example.com/user"
        )
        
        assert data.scopes == []
        assert data.icon is None
        assert data.is_active is True
    
    def test_update_request_partial(self):
        """Test partial update request."""
        from app.modules.oauth.schemas import OAuthProviderUpdateRequest
        
        data = OAuthProviderUpdateRequest(
            display_name="New Name",
            is_active=False
        )
        
        assert data.display_name == "New Name"
        assert data.is_active is False
        assert data.client_id is None
    
    def test_status_request(self):
        """Test status request schema."""
        from app.modules.oauth.schemas import OAuthProviderStatusRequest
        
        activate = OAuthProviderStatusRequest(is_active=True)
        deactivate = OAuthProviderStatusRequest(is_active=False)
        
        assert activate.is_active is True
        assert deactivate.is_active is False


class TestOAuthProviderPermissions:
    """Test OAuth provider permission constants."""
    
    def test_oauth_provider_permissions_exist(self):
        """Test that OAuth provider permissions are defined."""
        from app.constants.permissions import PermissionEnum
        
        assert hasattr(PermissionEnum, 'OAUTH_PROVIDERS_READ')
        assert hasattr(PermissionEnum, 'OAUTH_PROVIDERS_WRITE')
        assert hasattr(PermissionEnum, 'OAUTH_PROVIDERS_DELETE')
        
        assert PermissionEnum.OAUTH_PROVIDERS_READ.value == "oauth_providers:read"
        assert PermissionEnum.OAUTH_PROVIDERS_WRITE.value == "oauth_providers:write"
        assert PermissionEnum.OAUTH_PROVIDERS_DELETE.value == "oauth_providers:delete"


class TestOAuthProviderErrorCodes:
    """Test OAuth provider error codes."""
    
    def test_error_codes_exist(self):
        """Test that OAuth provider error codes are defined."""
        from app.constants.error_codes import ErrorCode
        
        assert hasattr(ErrorCode, 'OAUTH_PROVIDER_NOT_FOUND')
        assert hasattr(ErrorCode, 'OAUTH_PROVIDER_HAS_ACCOUNTS')
        assert hasattr(ErrorCode, 'DUPLICATE_ENTRY')

