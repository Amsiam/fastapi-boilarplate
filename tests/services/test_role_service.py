"""
Role and Permission Service tests.
"""
import pytest
from uuid import uuid4
from app.modules.roles.service import RoleService, PermissionService
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.roles.models import Role
from app.core.mongo import mongodb

@pytest.fixture(autouse=True)
async def setup_mongo_connection():
    """Ensure MongoDB connection is active for tests."""
    mongodb.connect()
    yield
    mongodb.close()

class TestRoleService:
    """Test RoleService with real database."""
    
    async def test_role_service_init(self, session):
        """Test RoleService initialization."""
        service = RoleService(session)
        assert service.db is session
    
    async def test_create_role_success(self, session):
        """Test successful role creation."""
        service = RoleService(session)
        
        role = await service.create_role(
            name="test_role_" + str(uuid4())[:8],
            description="Test role description",
            actor_id=uuid4()
        )
        
        assert role is not None
        assert "test_role_" in role.name
    
    async def test_create_role_duplicate(self, session):
        """Test creating role with duplicate name."""
        role_name = "duplicate_role_" + str(uuid4())[:8]
        
        # Create first role
        role = Role(name=role_name, description="First role")
        session.add(role)
        await session.commit()
        
        service = RoleService(session)
        
        with pytest.raises(ConflictError):
            await service.create_role(name=role_name, description="Duplicate role", actor_id=uuid4())
    
    async def test_get_role_not_found(self, session):
        """Test getting non-existent role."""
        service = RoleService(session)
        
        with pytest.raises(NotFoundError):
            await service.get_role(uuid4())
    
    async def test_list_roles_paginated(self, session):
        """Test listing roles with pagination."""
        service = RoleService(session)
        
        result = await service.list_roles(page=1, per_page=10)
        
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "per_page" in result


class TestPermissionService:
    """Test PermissionService with real database."""
    
    async def test_permission_service_init(self, session):
        """Test PermissionService initialization."""
        service = PermissionService(session)
        assert service.db is session
    
    async def test_create_permission_success(self, session):
        """Test successful permission creation."""
        service = PermissionService(session)
        
        permission = await service.create_permission(
            code="test_permission_" + str(uuid4())[:8],
            description="Test permission",
            actor_id=uuid4()
        )
        
        assert permission is not None
        assert "test_permission_" in permission.code
    
    async def test_list_permissions(self, session):
        """Test listing permissions."""
        service = PermissionService(session)
        
        permissions = await service.list_permissions()
        
        assert isinstance(permissions, list)
