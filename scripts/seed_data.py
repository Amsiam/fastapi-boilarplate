"""
Seed script for default roles, permissions, and OAuth providers.
Run this after database initialization to populate default data.

Usage:
    python scripts/seed_data.py
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import async_session_maker
from app.models.role import Role, Permission, RolePermission
from app.models.oauth import OAuthProvider
from app.constants import PermissionEnum
from uuid import uuid4


async def seed_permissions(session: AsyncSession):
    """Create default permissions."""
    print("Creating permissions...")
    
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
    
    created_permissions = {}
    for code, description in permissions_data:
        perm = Permission(
            id=uuid4(),
            code=code,
            description=description
        )
        session.add(perm)
        created_permissions[code] = perm
    
    await session.commit()
    print(f"✅ Created {len(permissions_data)} permissions")
    return created_permissions


async def seed_roles(session: AsyncSession, permissions: dict):
    """Create default roles with permissions."""
    print("Creating roles...")
    
    # SUPER_ADMIN role
    super_admin = Role(
        id=uuid4(),
        name="SUPER_ADMIN",
        description="Super administrator with all permissions",
        is_system_role=True
    )
    session.add(super_admin)
    
    # MANAGER role
    manager = Role(
        id=uuid4(),
        name="MANAGER",
        description="Manager with user and content management permissions",
        is_system_role=True
    )
    session.add(manager)
    
    manager_perms = [
        "users:read", "users:write",
        "orders:read", "orders:write",
        "products:read", "products:write"
    ]
    for perm_code in manager_perms:
        if perm_code in permissions:
            rp = RolePermission(
                role_id=manager.id,
                permission_id=permissions[perm_code].id
            )
            session.add(rp)
    
    # SUPPORT role
    support = Role(
        id=uuid4(),
        name="SUPPORT",
        description="Support staff with read-only access",
        is_system_role=True
    )
    session.add(support)
    
    support_perms = ["users:read", "orders:read"]
    for perm_code in support_perms:
        if perm_code in permissions:
            rp = RolePermission(
                role_id=support.id,
                permission_id=permissions[perm_code].id
            )
            session.add(rp)
    
    await session.commit()
    print("✅ Created 3 default roles (SUPER_ADMIN, MANAGER, SUPPORT)")


async def seed_oauth_providers(session: AsyncSession):
    """Create OAuth provider configurations."""
    print("Creating OAuth providers...")
    
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
    
    for provider_data in providers:
        provider = OAuthProvider(
            id=uuid4(),
            **provider_data
        )
        session.add(provider)
    
    await session.commit()
    print(f"✅ Created {len(providers)} OAuth providers")
    print("⚠️  Remember to update client_id and client_secret in the database!")


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
    print("\n📝 Next steps:")
    print("1. Update OAuth provider credentials in the database")
    print("2. Create your first SUPER_ADMIN user via API or database")
    print("3. Start using the authentication system!")


if __name__ == "__main__":
    asyncio.run(main())
