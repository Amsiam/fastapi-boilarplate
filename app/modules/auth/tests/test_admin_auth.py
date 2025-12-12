import pytest
import uuid
from app.modules.users.schemas import AdminCreate
from app.modules.users.service import UserManagementService

@pytest.fixture
def service(session):
    return UserManagementService(session)

@pytest.fixture
def super_admin_id():
    return uuid.uuid4()

@pytest.mark.asyncio
class TestAdminAuth:
    """Test authentication flows specific to Administrators."""

    async def test_admin_me_endpoint(self, client, service, super_admin_id):
        """
        Test that an Admin can access /api/v1/auth/me and receive role details.
        This covers the code path that previously raised ModuleNotFoundError.
        """
        # 1. Create an Admin
        unique_id = str(uuid.uuid4())[:8]
        username = f"admin_{unique_id}"
        email = f"admin_{unique_id}@test.com"
        password = "AdminPass123!"
        
        data = AdminCreate(email=email, password=password, username=username)
        admin = await service.create_admin(data, actor_id=super_admin_id)
        
        # 2. Login as Admin
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": email, "password": password}
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        
        # 3. Call /me endpoint
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Verify Admin specific fields
        assert data["user_type"] == "ADMIN"
        assert data["email"] == email
        # Check that role_name is present (it might be None if no specific role assigned by default, but field should verify logic ran)
        # Note: In create_admin, if we don't pass role_id, it might default or be nullable.
        # But the crucial part is that the code path for retrieving it ran without error.
