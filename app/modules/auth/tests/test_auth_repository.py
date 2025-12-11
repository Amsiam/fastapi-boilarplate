"""
Auth Repository tests.
"""
import pytest
from unittest.mock import AsyncMock

class TestAuthRepository:
    """Test auth-related repositories."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session
    
    async def test_refresh_token_repository_init(self, mock_session):
        """Test RefreshTokenRepository initialization."""
        from app.modules.auth.repository import RefreshTokenRepository
        
        repo = RefreshTokenRepository(mock_session)
        assert repo.db is mock_session
    
    async def test_oauth_provider_repository_init(self, mock_session):
        """Test OAuthProviderRepository initialization."""
        from app.modules.auth.repository import OAuthProviderRepository
        
        repo = OAuthProviderRepository(mock_session)
        assert repo.db is mock_session
    
    async def test_oauth_account_repository_init(self, mock_session):
        """Test OAuthAccountRepository initialization."""
        from app.modules.auth.repository import OAuthAccountRepository
        
        repo = OAuthAccountRepository(mock_session)
        assert repo.db is mock_session
