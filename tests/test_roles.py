"""
Role and Permission management tests.
Run with: pytest tests/test_roles.py -v
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.user import User
from app.constants.enums import UserRole


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user with all permissions."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    user.is_active = True
    user.is_verified = True
    return user


class TestRolesEndpointUnauthorized:
    """Test role endpoints without authentication."""
    
    async def test_list_roles_unauthorized(self, client):
        """Test listing roles without authentication."""
        response = await client.get("/api/v1/admin/roles")
        assert response.status_code == 401
    
    async def test_create_role_unauthorized(self, client):
        """Test creating role without authentication."""
        response = await client.post(
            "/api/v1/admin/roles",
            json={"name": "TEST_ROLE", "description": "Test"}
        )
        assert response.status_code == 401
    
    async def test_get_role_unauthorized(self, client):
        """Test getting role without authentication."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/admin/roles/{fake_id}")
        assert response.status_code == 401
    
    async def test_update_role_unauthorized(self, client):
        """Test updating role without authentication."""
        fake_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/v1/admin/roles/{fake_id}",
            json={"name": "UPDATED_ROLE"}
        )
        assert response.status_code == 401
    
    async def test_delete_role_unauthorized(self, client):
        """Test deleting role without authentication."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/v1/admin/roles/{fake_id}")
        assert response.status_code == 401


class TestPermissionsEndpointUnauthorized:
    """Test permission endpoints without authentication."""
    
    async def test_list_permissions_unauthorized(self, client):
        """Test listing permissions without authentication."""
        response = await client.get("/api/v1/admin/permissions")
        assert response.status_code == 401
    
    async def test_create_permission_unauthorized(self, client):
        """Test creating permission without authentication."""
        response = await client.post(
            "/api/v1/admin/permissions",
            json={"code": "test:action", "description": "Test"}
        )
        assert response.status_code == 401
    
    async def test_delete_permission_unauthorized(self, client):
        """Test deleting permission without authentication."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/v1/admin/permissions/{fake_id}")
        assert response.status_code == 401


class TestRoleValidation:
    """Test role endpoint validation (auth is checked before path validation)."""
    
    async def test_get_role_invalid_uuid(self, client):
        """Test getting role with invalid UUID returns 401 first (auth check)."""
        response = await client.get("/api/v1/admin/roles/not-a-uuid")
        # Auth is checked before path validation
        assert response.status_code == 401
    
    async def test_update_role_invalid_uuid(self, client):
        """Test updating role with invalid UUID returns 401 first."""
        response = await client.put(
            "/api/v1/admin/roles/not-a-uuid",
            json={"description": "TEST"}
        )
        assert response.status_code == 401
    
    async def test_delete_role_invalid_uuid(self, client):
        """Test deleting role with invalid UUID returns 401 first."""
        response = await client.delete("/api/v1/admin/roles/not-a-uuid")
        assert response.status_code == 401


class TestPermissionValidation:
    """Test permission endpoint validation (auth is checked before path validation)."""
    
    async def test_delete_permission_invalid_uuid(self, client):
        """Test deleting permission with invalid UUID returns 401 first."""
        response = await client.delete("/api/v1/admin/permissions/not-a-uuid")
        # Auth is checked before path validation
        assert response.status_code == 401
