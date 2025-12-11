"""
OAuth Provider Service tests.
"""
import pytest
from uuid import uuid4
from app.modules.oauth.provider_service import OAuthProviderService
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.oauth.models import OAuthProvider
from app.core.mongo import mongodb

@pytest.fixture(autouse=True)
async def setup_mongo_connection():
    """Ensure MongoDB connection is active for tests."""
    mongodb.connect()
    yield
    mongodb.close()

class TestOAuthProviderService:
    """Test OAuthProviderService with real database."""
    
    async def test_oauth_provider_service_init(self, session):
        """Test OAuthProviderService initialization."""
        service = OAuthProviderService(session)
        assert service.db is session
    
    async def test_create_provider_success(self, session):
        """Test successful provider creation."""
        service = OAuthProviderService(session)
        
        provider_name = "test_provider_" + str(uuid4())[:8]
        result = await service.create_provider(
            name=provider_name,
            display_name="Test Provider",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com",
            actor_id=uuid4()
        )
        
        assert result["name"] == provider_name
        assert result["display_name"] == "Test Provider"
        assert result["is_active"] is True
    
    async def test_create_provider_duplicate(self, session):
        """Test creating provider with duplicate name."""
        provider_name = "duplicate_provider_" + str(uuid4())[:8]
        
        # Create first provider
        provider = OAuthProvider(
            name=provider_name,
            display_name="First Provider",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com"
        )
        session.add(provider)
        await session.commit()
        
        service = OAuthProviderService(session)
        
        with pytest.raises(ConflictError):
            await service.create_provider(
                name=provider_name,
                display_name="Duplicate Provider",
                client_id="client456",
                client_secret="secret456",
                authorization_url="https://auth2.example.com",
                token_url="https://token2.example.com",
                user_info_url="https://userinfo2.example.com",
                actor_id=uuid4()
            )
    
    async def test_get_provider_success(self, session):
        """Test getting an existing provider."""
        # Create a provider
        provider = OAuthProvider(
            name="get_test_provider_" + str(uuid4())[:8],
            display_name="Get Test Provider",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com"
        )
        session.add(provider)
        await session.commit()
        await session.refresh(provider)
        
        service = OAuthProviderService(session)
        result = await service.get_provider(provider.id)
        
        assert result["id"] == str(provider.id)
        assert result["display_name"] == "Get Test Provider"
    
    async def test_get_provider_not_found(self, session):
        """Test getting non-existent provider."""
        service = OAuthProviderService(session)
        
        with pytest.raises(NotFoundError):
            await service.get_provider(uuid4())
    
    async def test_list_providers_paginated(self, session):
        """Test listing providers with pagination."""
        service = OAuthProviderService(session)
        
        result = await service.list_providers(page=1, per_page=10)
        
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "per_page" in result
    
    async def test_update_provider_status(self, session):
        """Test updating provider status."""
        # Create a provider
        provider = OAuthProvider(
            name="status_test_provider_" + str(uuid4())[:8],
            display_name="Status Test Provider",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com",
            is_active=True
        )
        session.add(provider)
        await session.commit()
        await session.refresh(provider)
        
        service = OAuthProviderService(session)
        
        # Deactivate
        result = await service.update_status(provider.id, False, actor_id=uuid4())
        assert result["is_active"] is False
        
        # Verify in database
        await session.refresh(provider)
        assert provider.is_active is False
        
        # Reactivate
        result = await service.update_status(provider.id, True, actor_id=uuid4())
        assert result["is_active"] is True
    
    async def test_update_provider_status_not_found(self, session):
        """Test updating status of non-existent provider."""
        service = OAuthProviderService(session)
        
        with pytest.raises(NotFoundError):
            await service.update_status(uuid4(), False, actor_id=uuid4())
    
    async def test_delete_provider_success(self, session):
        """Test successful provider deletion."""
        # Create a provider without linked accounts
        provider = OAuthProvider(
            name="delete_test_provider_" + str(uuid4())[:8],
            display_name="Delete Test Provider",
            client_id="client123",
            client_secret="secret123",
            authorization_url="https://auth.example.com",
            token_url="https://token.example.com",
            user_info_url="https://userinfo.example.com"
        )
        session.add(provider)
        await session.commit()
        await session.refresh(provider)
        
        provider_id = provider.id
        
        service = OAuthProviderService(session)
        await service.delete_provider(provider_id, actor_id=uuid4())
        
        # Verify deletion
        with pytest.raises(NotFoundError):
            await service.get_provider(provider_id)
    
    async def test_delete_provider_not_found(self, session):
        """Test deleting non-existent provider."""
        service = OAuthProviderService(session)
        
        with pytest.raises(NotFoundError):
            await service.delete_provider(uuid4(), actor_id=uuid4())
