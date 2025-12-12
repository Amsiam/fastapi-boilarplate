import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.modules.users.models import User, Admin
from app.core.security import get_password_hash, create_access_token
from app.constants.enums import UserType
from unittest.mock import patch

@pytest.mark.asyncio
async def test_oauth_providers_crud(client: AsyncClient, session):
    """
    Test OAuth Provider Admin CRUD: Create -> List -> Update -> Delete.
    """
    
    # 1. Setup Admin User
    user_id = uuid4()
    # We don't necessarily need to insert the user into DB if we Mock permissions
    # But for integration, it's better to have a real user if possible.
    # However, Role-based sub-permissions are checked via `get_user_permissions`.
    # We will mock `get_user_permissions` to return all OAuth permissions.
    
    # Insert user to ensure FK constraints if any (e.g. created_by)
    # The `create_provider` endpoint uses `actor_id=current_user.id`.
    user = User(
        id=user_id,
        email=f"oauth_admin_{uuid4()}@example.com",
        hashed_password=get_password_hash("password123"),
        user_type=UserType.ADMIN,
        is_active=True,
        is_verified=True
    )
    session.add(user)
    await session.commit()
    
    token = create_access_token(data={"sub": str(user_id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Permissions required: 
    # OAUTH_PROVIDERS_READ, OAUTH_PROVIDERS_WRITE, OAUTH_PROVIDERS_DELETE
    
    with patch("app.core.permissions.get_user_permissions", return_value=["*"]):
        
        # 2. Unknown Provider (Create)
        provider_name = f"provider_{uuid4().hex[:8]}"
        create_data = {
            "name": provider_name,
            "display_name": "Test Provider",
            "client_id": "client_id_123",
            "client_secret": "secret_456",
            "authorization_url": "https://test.com/auth",
            "token_url": "https://test.com/token",
            "user_info_url": "https://test.com/userinfo",
            "scopes": ["openid", "email"],
            "icon": "https://test.com/icon.png",
            "is_active": True
        }
        
        res = await client.post("/api/v1/admin/oauth-providers", json=create_data, headers=headers)
        assert res.status_code == 201, f"Create failed: {res.text}"
        data = res.json()["data"]
        assert data["name"] == provider_name
        provider_id = data["id"]
        
        # 3. List Providers
        res = await client.get("/api/v1/admin/oauth-providers", headers=headers)
        assert res.status_code == 200
        items = res.json()["data"]["items"]
        assert len(items) >= 1
        found = next((p for p in items if p["id"] == provider_id), None)
        assert found is not None
        assert found["display_name"] == "Test Provider"
        
        # 4. Get Provider Detail
        res = await client.get(f"/api/v1/admin/oauth-providers/{provider_id}", headers=headers)
        assert res.status_code == 200
        detail = res.json()["data"]
        assert detail["client_id"] == "client_id_123"
        # Secret typically not returned or masked? Check schema.
        # OAuthProviderDetailResponse usually includes it or masks it.
        # Let's check response.
        
        # 5. Update Provider
        update_data = {
            "display_name": "Updated Provider Name",
            "scopes": ["openid", "profile"]
        }
        res = await client.put(f"/api/v1/admin/oauth-providers/{provider_id}", json=update_data, headers=headers)
        assert res.status_code == 200, f"Update failed: {res.text}"
        
        # Verify update
        res = await client.get(f"/api/v1/admin/oauth-providers/{provider_id}", headers=headers)
        detail = res.json()["data"]
        assert detail["display_name"] == "Updated Provider Name"
        assert detail["scopes"] == ["openid", "profile"]
        
        # 6. Delete Provider
        res = await client.delete(f"/api/v1/admin/oauth-providers/{provider_id}", headers=headers)
        assert res.status_code == 200
        
        # Verify Deletion
        res = await client.get(f"/api/v1/admin/oauth-providers/{provider_id}", headers=headers)
        assert res.status_code == 404
