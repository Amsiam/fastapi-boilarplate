"""
Permissions Seeder - Seeds all system permissions from PermissionEnum.
"""
from sqlmodel import select
from seeders.base import BaseSeeder
from app.models.role import Permission
from app.constants import PermissionEnum


class PermissionsSeeder(BaseSeeder):
    """Seed all system permissions from PermissionEnum."""
    
    order = 10  # Run early - permissions are needed by roles
    
    async def should_run(self) -> bool:
        """Check if permissions need to be seeded."""
        result = await self.session.execute(select(Permission).limit(1))
        return result.first() is None
    
    async def run(self) -> None:
        """Create all permissions from PermissionEnum."""
        for perm in PermissionEnum:
            # Check if permission already exists
            result = await self.session.execute(
                select(Permission).where(Permission.code == perm.value)
            )
            if result.first():
                continue
            
            # Create permission
            permission = Permission(
                code=perm.value,
                description=perm.value.replace(":", " ").replace("_", " ").title()
            )
            self.session.add(permission)
        
        await self.session.commit()
        print(f"  ✅ Seeded {len(PermissionEnum)} permissions")
