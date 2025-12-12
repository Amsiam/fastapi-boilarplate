import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.modules.roles.models import Role, Permission
from app.core.security import create_access_token
from app.constants import PermissionEnum

@pytest.mark.asyncio
async def test_roles_crud_integration(client: AsyncClient, session):
    """
    Full CRUD integration test for Roles.
    Uses real DB (via client/session fixtures) and mocked Auth (via token generation).
    """
    
    # 1. Setup: Create Admin User and Token
    # We need a user with permissions. 
    # Since we don't have a full User fixture here easily, we can manually insert a user 
    # OR simpler: Generate a token for a random UUID and Mock the permission dependency?
    # NO. We want integration. We should mock the 'get_current_user' or 'require_permissions'
    # BUT conftest says 'client' uses 'main_app'.
    # If we want to test REAL auth logic, we need a real user in DB.
    
    # Let's seed a Super Admin directly in DB
    from app.modules.users.models import User, Admin
    from app.constants.enums import UserType
    from app.core.security import get_password_hash
    
    user_id = uuid4()
    user = User(
        id=user_id,
        email=f"admin_{uuid4()}@example.com",
        hashed_password=get_password_hash("password123"),
        user_type=UserType.ADMIN,
        is_active=True,
        is_verified=True
    )
    session.add(user)
    
    # We also need to give this user a Role that has permissions.
    # Or checking super_admin flag if logic allows. 
    # Admin endpoints check 'check_super_admin' or 'require_permissions'.
    # For Roles, it uses 'require_permissions'.
    # We need to assign valid permissions to this user.
    # For simplicity, let's patch `get_user_permissions` to return ["*"]
    # This keeps the test focused on ROLE CRUD, not Auth internals (which we test separately).
    
    await session.commit()
    
    # FIX: create_access_token expects data dict
    token = create_access_token(data={"sub": str(user_id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    # We will override `get_user_permissions` to allow access, 
    # effectively simulating a Super Admin for the purpose of testing the Role Endpoints logic.
    from unittest.mock import patch
    
    with patch("app.core.permissions.get_user_permissions", return_value=["*"]):
        
        # 2. CREATE ROLE
        role_data = {
            "name": f"Integration_Role_{uuid4()}",
            "description": "Integration Test Role",
            "permission_ids": [] 
        }
        res = await client.post("/api/v1/admin/roles", json=role_data, headers=headers)
        assert res.status_code == 201, f"Create failed: {res.text}"
        data = res.json()["data"]
        assert data["name"] == role_data["name"]
        role_id = data["id"]
        
        # 3. LIST ROLES
        res = await client.get("/api/v1/admin/roles", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        items = data["items"]
        assert len(items) >= 1
        # Verify fields that were missing before
        created_role = next((r for r in items if r["id"] == role_id), None)
        assert created_role is not None
        assert "description" in created_role, "Description missing in list response"
        assert "created_at" in created_role, "created_at missing in list response"
        assert "updated_at" in created_role, "updated_at missing in list response"
        assert created_role["description"] == "Integration Test Role"

        # 4. GET ROLE DETAILS
        res = await client.get(f"/api/v1/admin/roles/{role_id}", headers=headers)
        assert res.status_code == 200
        detail = res.json()["data"]
        assert detail["id"] == role_id
        assert detail["name"] == role_data["name"]

        # 5. UPDATE ROLE
        # Test update request schema fix
        update_data = {
            "name": f"Updated_Name_{uuid4()}",
            "description": "Updated Description"
        }
        res = await client.put(f"/api/v1/admin/roles/{role_id}", json=update_data, headers=headers)
        assert res.status_code == 200, f"Update failed: {res.text}"
        
        # Verify update
        res = await client.get(f"/api/v1/admin/roles/{role_id}", headers=headers)
        updated_detail = res.json()["data"]
        assert updated_detail["name"] == update_data["name"]
        assert updated_detail["description"] == update_data["description"]

        # 6. DELETE ROLE
        res = await client.delete(f"/api/v1/admin/roles/{role_id}", headers=headers)
        assert res.status_code == 200
        
        # Verify deletion
        res = await client.get(f"/api/v1/admin/roles/{role_id}", headers=headers)
        assert res.status_code == 404

@pytest.mark.asyncio
async def test_permissions_list_integration(client: AsyncClient, session):
    """Verify list_permissions response structure."""
    from app.modules.users.models import User
    from app.constants.enums import UserType
    from app.core.security import get_password_hash
    
    user_id = uuid4()
    user = User(
         id=user_id,
        email=f"admin_perm_{uuid4()}@example.com",
        hashed_password=get_password_hash("pass"),
        user_type=UserType.ADMIN,
        is_active=True,
        is_verified=True
    )
    session.add(user)
    await session.commit()
    
    # FIX: create_access_token expects data dict
    token = create_access_token(data={"sub": str(user_id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    from unittest.mock import patch
    with patch("app.core.permissions.get_user_permissions", return_value=["*"]):
        res = await client.get("/api/v1/admin/permissions", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert isinstance(data, list), "Permissions should be a list, not paginated dict"
        if len(data) > 0:
            assert "code" in data[0]
            assert "description" in data[0]
