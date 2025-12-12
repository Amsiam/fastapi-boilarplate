import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.modules.roles.models import Role
from app.core.security import create_access_token, get_password_hash
from app.constants.enums import UserType

@pytest.mark.asyncio
async def test_users_integration(client: AsyncClient, session):
    """
    CRUD integration for Admins and Customers.
    """
    # Setup Super Admin
    from app.modules.users.models import User
    
    # Create Role first
    role = Role(name="TEST_ADMIN_ROLE", description="Test Role", is_system=False)
    session.add(role)
    await session.commit() # commit to get ID
    
    # Create Super Admin User
    admin_id = uuid4()
    admin_user = User(
        id=admin_id,
        email=f"superadmin_{uuid4()}@example.com",
        hashed_password=get_password_hash("password123"),
        user_type=UserType.ADMIN,
        is_active=True,
        is_verified=True
    )
    session.add(admin_user)
    await session.commit()
    
    token = create_access_token(data={"sub": str(admin_id), "user_type": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Patch permissions to allow SUPER ADMIN power
    from unittest.mock import patch
    with patch("app.core.permissions.get_user_permissions", return_value=["*"]):
        
        # --- ADMIN CRUD ---
        
        # 1. Create Admin
        new_admin_data = {
            "email": f"new_admin_{uuid4()}@example.com",
            "password": "securepassword123",
            "username": f"adminuser_{uuid4().hex[:8]}",
            "role_id": str(role.id)
        }
        res = await client.post("/api/v1/admin/admins/", json=new_admin_data, headers=headers)
        assert res.status_code == 201, f"Create Admin failed: {res.text}"
        data = res.json()["data"]
        created_id = data["id"]
        assert data["email"] == new_admin_data["email"]
        assert data["username"] == new_admin_data["username"]
        assert "created_at" in data
        assert "updated_at" in data
        
        # 2. List Admins
        res = await client.get("/api/v1/admin/admins/", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        items = data["items"]
        assert isinstance(items, list)
        found = next((i for i in items if i["id"] == created_id), None)
        assert found is not None
        assert "created_at" in found, "Admin list missing created_at"

        # 3. Get Admin
        res = await client.get(f"/api/v1/admin/admins/{created_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["id"] == created_id
        
        # 4. Update Admin
        update_data = {"username": f"updated_{uuid4().hex[:8]}"}
        res = await client.put(f"/api/v1/admin/admins/{created_id}", json=update_data, headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["username"] == update_data["username"]
        
        # 5. Delete Admin
        res = await client.delete(f"/api/v1/admin/admins/{created_id}", headers=headers)
        assert res.status_code == 200
        
        # Verify Delete
        res = await client.get(f"/api/v1/admin/admins/{created_id}", headers=headers)
        assert res.status_code == 404
        
        
        # --- CUSTOMER CRUD ---
        
        # 1. Create Customer
        cust_data = {
            "email": f"customer_{uuid4()}@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "1234567890"
        }
        res = await client.post("/api/v1/admin/customers/", json=cust_data, headers=headers)
        assert res.status_code == 201, f"Create Customer failed: {res.text}"
        data = res.json()["data"]
        cust_id = data["id"]
        assert data["first_name"] == "John"
        assert "created_at" in data
        
        # 2. List Customers
        res = await client.get("/api/v1/admin/customers/", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        items = data["items"]
        found = next((i for i in items if i["id"] == cust_id), None)
        assert found is not None
        assert "phone_number" in found
        
        # 3. Update Customer
        update_cust = {"first_name": "Jane"}
        res = await client.put(f"/api/v1/admin/customers/{cust_id}", json=update_cust, headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["first_name"] == "Jane"
        
        # 4. Delete Customer
        res = await client.delete(f"/api/v1/admin/customers/{cust_id}", headers=headers)
        assert res.status_code == 200
        res = await client.get(f"/api/v1/admin/customers/{cust_id}", headers=headers)
        assert res.status_code == 404
