
import pytest
import asyncio
from uuid import uuid4
from app.core.permissions import get_user_permissions
from app.modules.roles.service import RoleService, PermissionService
from app.modules.users.service import UserManagementService
from app.core.cache import get_cache, set_cache, delete_cache, user_permissions_key

@pytest.mark.asyncio
async def test_permission_caching_lag(session, client):
    """
    Test that permissions are cached and updating the role does not immediately define the cache
    (demonstrating the lag / bug we want to fix).
    """
    role_service = RoleService(session)
    perm_service = PermissionService(session)
    user_service = UserManagementService(session)
    
    # 1. Setup: Create Role, Permission, and Admin User
    actor_id = uuid4()
    
    # Create Permission
    perm_code = f"test:perm:{uuid4()}"
    perm = await perm_service.create_permission(code=perm_code, actor_id=actor_id)
    
    # Create Role with this permission
    role_name = f"TestRole_{uuid4()}"
    role = await role_service.create_role(
        name=role_name,
        actor_id=actor_id,
        permission_ids=[perm.id]
    )
    
    # Create Admin User assigned to this role
    email = f"admin_{uuid4()}@example.com"
    # We need a user first... 
    from app.modules.users.schemas import AdminCreate
    
    user = await user_service.create_admin(
        data=AdminCreate(
            email=email,
            password="password123",
            username=f"admin_{uuid4()}",
            role_id=role.id
        ),
        actor_id=actor_id
    )

    # Fetch actual User DB object
    from app.modules.users.repository import UserRepository
    user_repo = UserRepository(session)
    user_db = await user_repo.get(user.user_id)
    
    # DEBUG: Check if RolePermission exists
    from app.modules.roles.models import RolePermission
    from sqlmodel import select
    res = await session.execute(select(RolePermission).where(RolePermission.role_id == role.id))
    rps = res.all()
    print(f"\n[DEBUG] RolePermissions found: {len(rps)}")
    for rp in rps:
        print(f"[DEBUG] RP: {rp}")

    # DEBUG: Check Admin record
    from app.modules.users.models import Admin
    res_admin = await session.execute(select(Admin).where(Admin.user_id == user.user_id))
    admin_rec = res_admin.scalar_one_or_none()
    print(f"\n[DEBUG] Admin Record: {admin_rec}")
    if admin_rec:
        print(f"[DEBUG] Admin RoleID: {admin_rec.role_id}")
        print(f"[DEBUG] Expected RoleID: {role.id}")

    # 2. First Access: Should cache permissions
    # We pass the user object. get_user_permissions needs 'db' session.
    perms = await get_user_permissions(user_db, session)
    print(f"[DEBUG] User Perms: {perms}")
    assert perm_code in perms
    
    # Verify it is in Redis
    cache_key = user_permissions_key(str(user_db.id))
    cached = await get_cache(cache_key)
    assert cached is not None
    if isinstance(cached, dict):
        assert perm_code in cached["permissions"]
    else:
        assert perm_code in cached
    
    # 3. Update Role: Remove the permission
    # Update role to have NO permissions
    await role_service.update_role(
        role_id=role.id,
        actor_id=actor_id,
        permission_ids=[]
    )
    
    # 4. Second Access: CACHE INVALIDATION EXPECTED
    # With our fix, this will return fresh data (empty permissions)
    perms_after = await get_user_permissions(user_db, session)
    
    # Verify Fix
    if perm_code in perms_after:
        pytest.fail("Cache Lag Detected! Permission still present after removal.")
    else:
        print("\n[SUCCESS] Cache Invalidation Works! Permission removed.")
    
    assert perm_code not in perms_after, "Permission should be removed immediately"

