"""
Role Repository tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestRoleRepository:
    """Test RoleRepository functionality."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session
    
    async def test_role_repository_init(self, mock_session):
        """Test RoleRepository initialization."""
        from app.modules.roles.repository import RoleRepository
        
        repo = RoleRepository(mock_session)
        assert repo.db is mock_session
    
    async def test_get_by_name_not_found(self, mock_session):
        """Test getting role by name when not found."""
        from app.modules.roles.repository import RoleRepository
        
        # Mock execute to return empty result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        repo = RoleRepository(mock_session)
        role = await repo.get_by_name("NONEXISTENT")
        assert role is None
