"""
Repository layer unit tests.
Run with: pytest tests/test_repositories.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestBaseRepository:
    """Test BaseRepository functionality."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session
    
    async def test_base_repository_init(self, mock_session):
        """Test BaseRepository initialization."""
        from app.repositories.base import BaseRepository
        from app.models.user import User
        
        repo = BaseRepository(User, mock_session)
        assert repo.model == User
        assert repo.db is mock_session


class TestUserRepository:
    """Test UserRepository functionality."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session
    
    async def test_user_repository_init(self, mock_session):
        """Test UserRepository initialization."""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(mock_session)
        assert repo.db is mock_session
    
    async def test_get_by_email_not_found(self, mock_session):
        """Test getting user by email when not found."""
        from app.repositories.user_repository import UserRepository
        
        # Mock execute to return empty result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        repo = UserRepository(mock_session)
        user = await repo.get_by_email("nonexistent@example.com")
        assert user is None


class TestRoleRepository:
    """Test RoleRepository functionality."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session
    
    async def test_role_repository_init(self, mock_session):
        """Test RoleRepository initialization."""
        from app.repositories.role_repository import RoleRepository
        
        repo = RoleRepository(mock_session)
        assert repo.db is mock_session
    
    async def test_get_by_name_not_found(self, mock_session):
        """Test getting role by name when not found."""
        from app.repositories.role_repository import RoleRepository
        
        # Mock execute to return empty result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        repo = RoleRepository(mock_session)
        role = await repo.get_by_name("NONEXISTENT")
        assert role is None


class TestAuthRepository:
    """Test auth-related repositories."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session
    
    async def test_refresh_token_repository_init(self, mock_session):
        """Test RefreshTokenRepository initialization."""
        from app.repositories.auth_repository import RefreshTokenRepository
        
        repo = RefreshTokenRepository(mock_session)
        assert repo.db is mock_session
    
    async def test_oauth_provider_repository_init(self, mock_session):
        """Test OAuthProviderRepository initialization."""
        from app.repositories.auth_repository import OAuthProviderRepository
        
        repo = OAuthProviderRepository(mock_session)
        assert repo.db is mock_session
    
    async def test_oauth_account_repository_init(self, mock_session):
        """Test OAuthAccountRepository initialization."""
        from app.repositories.auth_repository import OAuthAccountRepository
        
        repo = OAuthAccountRepository(mock_session)
        assert repo.db is mock_session

