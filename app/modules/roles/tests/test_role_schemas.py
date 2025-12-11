"""
Role Schema tests.
"""
from app.modules.roles.schemas import (
    RoleCreateRequest,
    RoleUpdateRequest,
    PermissionCreateRequest
)

class TestRoleSchemas:
    """Test role-related schemas."""
    
    def test_role_create_request(self):
        """Test valid role creation."""
        data = RoleCreateRequest(
            name="CUSTOM_ROLE",
            description="A custom role"
        )
        assert data.name == "CUSTOM_ROLE"
    
    def test_role_update_request(self):
        """Test valid role update (no name field in update)."""
        data = RoleUpdateRequest(
            description="Updated description"
        )
        assert data.description == "Updated description"
    
    def test_permission_create_request(self):
        """Test valid permission creation."""
        data = PermissionCreateRequest(
            code="custom:action",
            description="Custom permission",
            resource="custom",
            action="action"
        )
        assert data.code == "custom:action"
        assert data.resource == "custom"
