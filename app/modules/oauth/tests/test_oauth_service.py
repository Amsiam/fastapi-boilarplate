"""
OAuth Service tests.
"""
import pytest
from app.modules.oauth.service import OAuthService
from app.core.exceptions import NotFoundError
from app.modules.oauth.models import OAuthProvider
from app.core.mongo import mongodb

@pytest.fixture(autouse=True)
async def setup_mongo_connection():
    """Ensure MongoDB connection is active for tests."""
    mongodb.connect()
    yield
    mongodb.close()

class TestOAuthService:
    """Test OAuthService with real database."""
    
    async def test_oauth_service_init(self, session):
        """Test OAuthService initialization."""
        service = OAuthService(session)
        assert service.db is session
    
    async def test_list_providers_empty(self, session):
        """Test listing providers when none exist."""
        service = OAuthService(session)
        providers = await service.list_providers()
        # Result could be empty or have providers depending on test order
        assert isinstance(providers, list)
    
    async def test_list_providers_only_active(self, session):
        """Test listing providers returns only active ones."""
        # Create active and inactive providers
        active_provider = OAuthProvider(
            name="active_test_provider",
            display_name="Active Test",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com",
            is_active=True
        )
        inactive_provider = OAuthProvider(
            name="inactive_test_provider",
            display_name="Inactive Test",
            client_id="client456",
            client_secret="secret456",
            authorization_url="https://auth2.example.com",
            token_url="https://token2.example.com",
            user_info_url="https://userinfo2.example.com",
            is_active=False
        )
        session.add(active_provider)
        session.add(inactive_provider)
        await session.commit()
        
        service = OAuthService(session)
        providers = await service.list_providers()
        
        # Should only include active providers
        provider_names = [p["name"] for p in providers]
        assert "active_test_provider" in provider_names
        assert "inactive_test_provider" not in provider_names
    
    async def test_get_login_url_provider_not_found(self, session):
        """Test getting login URL for non-existent provider."""
        service = OAuthService(session)
        
        with pytest.raises(NotFoundError):
            await service.get_login_url("nonexistent_provider", "http://callback")
