import pytest
from uuid import uuid4
from fastapi import Request
from app.modules.roles.service import RoleService, PermissionService
from app.modules.oauth.provider_service import OAuthProviderService
from app.modules.audit.service import audit_service
from app.core.mongo import mongodb

@pytest.fixture
def role_service(session):
    return RoleService(session)

@pytest.fixture
def perm_service(session):
    return PermissionService(session)

@pytest.fixture
def oauth_service(session):
    return OAuthProviderService(session)

@pytest.fixture
def actor_id():
    return uuid4()



@pytest.mark.asyncio
async def test_role_audit(role_service, actor_id):
    """Test audit logs for role creation and deletion."""
    # Create Role
    role = await role_service.create_role(
        name="AUDIT_ROLE",
        description="Test Role",
        actor_id=actor_id
    )
    
    # Verify Create Log
    db = mongodb.get_db()
    logs = await db["audit_logs"].find({"target_id": str(role.id), "action": "create_role"}).to_list(length=1)
    assert len(logs) == 1
    assert logs[0]["actor_id"] == str(actor_id)
    assert logs[0]["details"]["name"] == "AUDIT_ROLE"
    
    # Update Role
    await role_service.update_role(
        role_id=role.id,
        actor_id=actor_id,
        description="Updated Description"
    )
    
    # Verify Update Log
    logs = await db["audit_logs"].find({"target_id": str(role.id), "action": "update_role"}).to_list(length=1)
    assert len(logs) == 1
    assert logs[0]["old_values"]["description"] == "Test Role"
    assert logs[0]["new_values"]["description"] == "Updated Description"
    
    # Delete Role
    await role_service.delete_role(role_id=role.id, actor_id=actor_id)
    
    # Verify Delete Log
    logs = await db["audit_logs"].find({"target_id": str(role.id), "action": "delete_role"}).to_list(length=1)
    assert len(logs) == 1

@pytest.mark.asyncio
async def test_permission_audit(perm_service, actor_id):
    """Test audit logs for permission creation and deletion."""
    # Create Permission
    perm = await perm_service.create_permission(
        code="audit:test",
        description="Test Permission",
        actor_id=actor_id
    )
    
    # Verify Create Log
    db = mongodb.get_db()
    logs = await db["audit_logs"].find({"target_id": str(perm.id), "action": "create_permission"}).to_list(length=1)
    assert len(logs) == 1
    assert logs[0]["details"]["code"] == "audit:test"
    
    # Delete Permission
    await perm_service.delete_permission(permission_id=perm.id, actor_id=actor_id)
    
    # Verify Delete Log
    logs = await db["audit_logs"].find({"target_id": str(perm.id), "action": "delete_permission"}).to_list(length=1)
    assert len(logs) == 1

@pytest.mark.asyncio
async def test_oauth_provider_audit(oauth_service, actor_id):
    """Test audit logs for OAuth provider operations."""
    # Create Provider
    provider = await oauth_service.create_provider(
        name="audit_provider",
        display_name="Audit Provider",
        client_id="client_id",
        client_secret="secret",
        authorization_url="http://auth",
        token_url="http://token",
        user_info_url="http://userinfo",
        actor_id=actor_id
    )
    
    # Verify Create Log
    db = mongodb.get_db()
    logs = await db["audit_logs"].find({"target_id": provider["id"], "action": "create_oauth_provider"}).to_list(length=1)
    assert len(logs) == 1
    assert logs[0]["details"]["name"] == "audit_provider"
    
    # Update Status
    await oauth_service.update_status(provider_id=provider["id"], is_active=False, actor_id=actor_id)
    
    # Verify Status Update Log
    logs = await db["audit_logs"].find({"target_id": provider["id"], "action": "update_oauth_provider_status"}).to_list(length=1)
    assert len(logs) == 1
    assert logs[0]["old_values"]["is_active"] is True
    assert logs[0]["new_values"]["is_active"] is False

@pytest.mark.asyncio
async def test_audit_list_logs(role_service, actor_id):
    """Test list_logs functionality in AuditService."""
    # Generate some logs
    await role_service.create_role(name="LOG_ROLE_1", actor_id=actor_id)
    await role_service.create_role(name="LOG_ROLE_2", actor_id=actor_id)
    
    # List Logs
    logs, total = await audit_service.list_logs(filters={"actor_id": str(actor_id)})
    
    assert total >= 2
    assert len(logs) >= 2
    assert logs[0]["action"] == "create_role"
    assert logs[0]["actor_id"] == str(actor_id)

@pytest.fixture
def auth_service(session):
    from app.modules.auth.service import AuthService
    return AuthService(session)

@pytest.mark.asyncio
async def test_auth_audit(auth_service, session):
    """Test audit logs for user registration and login."""
    from app.core.security import hash_password
    from app.modules.users.models import User
    from app.constants.enums import UserType
    
    # Register Customer
    # Assuming 'admin' object is defined elsewhere in the test setup or context
    # and this line is intended to be inserted here.
    email = f"audit_auth_{uuid4()}@example.com"
    user = await auth_service.register_customer(
        email=email,
        password="password123",
        first_name="Audit",
        last_name="User"
    )
    
    # Verify Register Log
    db = mongodb.get_db()
    logs = await db["audit_logs"].find({"target_id": str(user.id), "action": "register_customer"}).to_list(length=1)
    assert len(logs) == 1
    assert logs[0]["details"]["email"] == email
    
    # Verify Email (Manually for login)
    await auth_service.verify_email(str(user.id))
    
    # Login
    await auth_service.authenticate_user(email, "password123")
    
    # Verify Login Log
    logs = await db["audit_logs"].find({"target_id": str(user.id), "action": "user_login"}).to_list(length=1)
    assert len(logs) == 1
    assert logs[0]["details"]["email"] == email
    
    # Logout
    await auth_service.logout(str(user.id))
    
    # Verify Logout Log
    logs = await db["audit_logs"].find({"target_id": str(user.id), "action": "user_logout"}).to_list(length=1)
    assert len(logs) == 1

