"""
User Repository tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestUserRepository:
    """Test UserRepository functionality."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session
    
    async def test_user_repository_init(self, mock_session):
        """Test UserRepository initialization."""
        from app.modules.users.repository import UserRepository
        
        repo = UserRepository(mock_session)
        assert repo.db is mock_session
    
    async def test_get_by_email_not_found(self, mock_session):
        """Test getting user by email when not found."""
        from app.modules.users.repository import UserRepository
        
        # Mock execute to return empty result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        repo = UserRepository(mock_session)
        user = await repo.get_by_email("nonexistent@example.com")
        assert user is None
