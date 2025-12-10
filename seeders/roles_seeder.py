"""
Roles Seeder - Seeds default system roles.
"""
from sqlmodel import select
from seeders.base import BaseSeeder
from app.models.role import Role, Permission


class RolesSeeder(BaseSeeder):
    """Seed default system roles."""
    
    order = 20  # After permissions
    
    DEFAULT_ROLES = [
        {
            "name": "SUPER_ADMIN",
            "description": "Super Administrator with all permissions",
            "is_system": True,
            "permissions": ["*"]  # All permissions
        },
        {
            "name": "ADMIN",
            "description": "Administrator",
            "is_system": True,
            "permissions": [
                "users:read", "users:write",
                "roles:read",
                "permissions:read",
                "audit_logs:read",
                "oauth_providers:read",
            ]
        },
        {
            "name": "MODERATOR",
            "description": "Moderator with limited admin access",
            "is_system": True,
            "permissions": [
                "users:read",
                "audit_logs:read",
            ]
        }
    ]
    
    async def should_run(self) -> bool:
        """Check if roles need to be seeded."""
        result = await self.session.execute(
            select(Role).where(Role.name == "SUPER_ADMIN")
        )
        return result.first() is None
    
    async def run(self) -> None:
        """Create default roles with permissions."""
        # Get all permissions
        result = await self.session.execute(select(Permission))
        all_permissions = {p.code: p for p in result.scalars().all()}
        
        for role_data in self.DEFAULT_ROLES:
            # Check if role exists
            result = await self.session.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            if result.first():
                continue
            
            # Create role
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                is_system=role_data["is_system"]
            )
            
            # Assign permissions
            perm_codes = role_data["permissions"]
            if "*" in perm_codes:
                # All permissions
                role.permissions = list(all_permissions.values())
            else:
                role.permissions = [
                    all_permissions[code] for code in perm_codes 
                    if code in all_permissions
                ]
            
            self.session.add(role)
        
        await self.session.commit()
        print(f"  ✅ Seeded {len(self.DEFAULT_ROLES)} roles")
