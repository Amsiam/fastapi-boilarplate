import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.modules.users.models import User, Admin
from app.core.security import get_password_hash
from app.constants.enums import UserType
from app.modules.roles.models import Role
from app.constants.permissions import PermissionEnum, DEFAULT_ROLE_PERMISSIONS

@pytest.mark.asyncio
async def test_audit_integration(client: AsyncClient, session):
    """
    Integration tests for Audit Logs.
    """
    
    # 1. Setup Admin with Permissions
    # Create Role with AUDIT_READ
    # Note: Super Admin bypasses checks, but let's test permission explicitly if possible.
    # We'll use a Super Admin for simplicity first, or a role with permissions.
    
    # Create Permission if not exists (usually seeded). 
    # But integration test DB is empty-ish.
    # Assuming PermissionEnum.AUDIT_READ exists.
    
    role = Role(name="AUDIT_ADMIN_ROLE", description="Audit Admin", is_system=False)
    session.add(role)
    await session.commit()
    
    # Endpoint checks current_user.user_type == UserType.ADMIN, so no specific permission needed yet.
    
    password = "strongpassword123"
    admin_id = uuid4()
    admin_email = f"audit_admin_{uuid4()}@example.com"
    
    admin_user = User(
        id=admin_id,
        email=admin_email,
        hashed_password=get_password_hash(password),
        user_type=UserType.ADMIN,
        is_active=True,
        is_verified=True
    )
    session.add(admin_user)
    
    admin_profile = Admin(
        user_id=admin_id,
        username=f"audit_admin_{uuid4().hex[:8]}",
        role_id=role.id
    )
    session.add(admin_profile)
    await session.commit()
    
    # 2. Login to get Token
    res = await client.post("/api/v1/auth/login", json={
        "username": admin_email,
        "password": password
    })
    assert res.status_code == 200
    token = res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Perform some actions to generate logs (Login generated one!)
    # `user_login` action should be in logs.
    
    # 4. List Logs
    # Path is /api/v1/admin/audit-logs/ (trailing slash required)
    res = await client.get("/api/v1/admin/audit-logs/", headers=headers)
        
    assert res.status_code == 200, f"List logs failed: {res.text}"
    data = res.json()["data"]
    items = data["items"]
    assert len(items) > 0
    
    # Verify the login log is there
    found_login = False
    for log in items:
        if log["action"] == "user_login" and log["actor_id"] == str(admin_id):
            found_login = True
            break
    assert found_login, "Login audit log not found"
    
    # 5. Test Filtering
    res = await client.get("/api/v1/admin/audit-logs/?action=user_login", headers=headers)
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    for log in items:
        assert log["action"] == "user_login"
