"""
Repository layer unit tests.
Run with: pytest tests/repositories/test_repositories.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
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
        from app.core.base_repository import BaseRepository
        from app.modules.users.models import User
        
        repo = BaseRepository(User, mock_session)
        assert repo.model == User
        assert repo.db is mock_session
