"""
Seed script for default roles, permissions, and OAuth providers.
Run this after database initialization to populate default data.

Usage:
    python scripts/seed_data.py
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import async_session_maker
from app.models.role import Role, Permission, RolePermission
from app.models.oauth import OAuthProvider
from uuid import uuid4


async def seed_permissions(session: AsyncSession) -> Dict[str, Permission]:
    """Create default permissions if they don't exist."""
    print("Checking permissions...")
    
    permissions_data = [
        # User permissions
        ("users:read", "View users"),
        ("users:write", "Create/update users"),
        ("users:delete", "Delete users"),
        
        # Role permissions
        ("roles:read", "View roles"),
        ("roles:write", "Create/update roles"),
        ("roles:delete", "Delete roles"),
        
        # Permission permissions
        ("permissions:read", "View permissions"),
        ("permissions:write", "Create/update permissions"),
        ("permissions:delete", "Delete permissions"),
        
        # Admin management
        ("admins:manage", "Manage admin users"),
        
        # Order permissions
        ("orders:read", "View orders"),
        ("orders:write", "Create/update orders"),
        
        # Product permissions
        ("products:read", "View products"),
        ("products:write", "Create/update products"),
        
        # System permissions
        ("system:config", "Configure system settings"),
        
        # Profile permissions
        ("profile:read", "View own profile"),
        ("profile:write", "Update own profile"),
    ]
    
    existing_permissions = {}
    
    # Check existing permissions
    result = await session.execute(select(Permission))
    for perm in result.scalars().all():
        existing_permissions[perm.code] = perm
    
    created_count = 0
    for code, description in permissions_data:
        if code not in existing_permissions:
            perm = Permission(
                id=uuid4(),
                code=code,
                description=description
            )
            session.add(perm)
            existing_permissions[code] = perm
            created_count += 1
    
    await session.commit()
    if created_count > 0:
        print(f"✅ Created {created_count} new permissions")
    else:
        print("✅ Permissions up to date")
        
    return existing_permissions


async def get_or_create_role(
    session: AsyncSession, 
    name: str, 
    description: str, 
    is_system: bool = False
) -> Role:
    """Get existing role or create new one."""
    result = await session.execute(select(Role).where(Role.name == name))
    role = result.scalar_one_or_none()
    
    if not role:
        role = Role(
            id=uuid4(),
            name=name,
            description=description,
            is_system=is_system
        )
        session.add(role)
        await session.commit()
        await session.refresh(role)
        print(f"✅ Created role: {name}")
    else:
        # Update is_system if needed
        if role.is_system != is_system:
            role.is_system = is_system
            session.add(role)
            await session.commit()
            await session.refresh(role)
            print(f"Updated role {name} is_system={is_system}")
            
    return role


async def assign_permissions(
    session: AsyncSession, 
    role: Role, 
    permission_codes: list[str], 
    all_permissions: Dict[str, Permission]
):
    """Assign permissions to role if not already assigned."""
    # Get existing role permissions
    result = await session.execute(
        select(RolePermission).where(RolePermission.role_id == role.id)
    )
    existing_links = {(rp.role_id, rp.permission_id) for rp in result.scalars().all()}
    
    added_count = 0
    for code in permission_codes:
        if code in all_permissions:
            perm = all_permissions[code]
            if (role.id, perm.id) not in existing_links:
                rp = RolePermission(
                    role_id=role.id,
                    permission_id=perm.id
                )
                session.add(rp)
                existing_links.add((role.id, perm.id))
                added_count += 1
    
    if added_count > 0:
        await session.commit()
        print(f"   - Added {added_count} permissions to {role.name}")


async def seed_roles(session: AsyncSession, permissions: Dict[str, Permission]):
    """Create default roles with permissions."""
    print("Checking roles...")
    
    # 1. SUPER_ADMIN role (All permissions)
    super_admin = await get_or_create_role(
        session,
        name="SUPER_ADMIN",
        description="Super administrator with all permissions",
        is_system=True
    )
    # Assign ALL permissions
    await assign_permissions(
        session, 
        super_admin, 
        list(permissions.keys()), 
        permissions
    )
    
    # 2. MANAGER role
    manager = await get_or_create_role(
        session,
        name="MANAGER",
        description="Manager with user and content management permissions",
        is_system=True
    )
    manager_perms = [
        "users:read", "users:write",
        "orders:read", "orders:write",
        "products:read", "products:write"
    ]
    await assign_permissions(session, manager, manager_perms, permissions)
    
    # 3. SUPPORT role
    support = await get_or_create_role(
        session,
        name="SUPPORT",
        description="Support staff with read-only access",
        is_system=True
    )
    support_perms = ["users:read", "orders:read"]
    await assign_permissions(session, support, support_perms, permissions)


async def seed_oauth_providers(session: AsyncSession):
    """Create OAuth provider configurations."""
    print("Checking OAuth providers...")
    
    providers = [
        {
            "name": "google",
            "display_name": "Google",
            "client_id": "YOUR_GOOGLE_CLIENT_ID",
            "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scopes": ["openid", "email", "profile"],
            "icon": "https://www.google.com/favicon.ico"
        },
        {
            "name": "github",
            "display_name": "GitHub",
            "client_id": "YOUR_GITHUB_CLIENT_ID",
            "client_secret": "YOUR_GITHUB_CLIENT_SECRET",
            "authorization_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "user_info_url": "https://api.github.com/user",
            "scopes": ["user:email"],
            "icon": "https://github.com/favicon.ico"
        }
    ]
    
    created_count = 0
    for provider_data in providers:
        # Check if provider exists
        result = await session.execute(
            select(OAuthProvider).where(OAuthProvider.name == provider_data["name"])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            provider = OAuthProvider(
                id=uuid4(),
                **provider_data
            )
            session.add(provider)
            created_count += 1
    
    await session.commit()
    if created_count > 0:
        print(f"✅ Created {created_count} new OAuth providers")
    else:
        print("✅ OAuth providers up to date")


async def main():
    """Run all seed functions."""
    print("🌱 Seeding database with default data...\n")
    
    async with async_session_maker() as session:
        # Seed permissions
        permissions = await seed_permissions(session)
        
        # Seed roles
        await seed_roles(session, permissions)
        
        # Seed OAuth providers
        await seed_oauth_providers(session)
    
    print("\n✅ Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
